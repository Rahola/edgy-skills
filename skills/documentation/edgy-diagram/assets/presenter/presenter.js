/* EDGY presenter-lite (edgy-diagram 2.8.0, extension contract 1).
 * Five effects, no more (a sixth goes to F6b): card wall → zoom, cross-view highlight,
 * search, current ↔ target filter over change annotations, paging. No network, no eval,
 * text only through textContent. Every animation is a cut with prefers-reduced-motion. */
(function () {
  'use strict';
  var errors = 0;
  window.addEventListener('error', function () { errors += 1; });

  function readJSON(id) {
    var el = document.getElementById(id);
    try { return JSON.parse(el ? el.textContent : 'null'); } catch (e) { return null; }
  }
  var graph = readJSON('edgy-graph') || { elements: [], relationships: [] };
  var views = readJSON('edgy-views') || [];
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var $ = function (sel, root) { return (root || document).querySelector(sel); };
  var $$ = function (sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); };
  var SVGNS = 'http://www.w3.org/2000/svg';

  // ---- model ---------------------------------------------------------------------------------------
  var byId = {};
  graph.elements.forEach(function (e) { byId[e.id] = e; });
  var near = {};
  graph.relationships.forEach(function (r) {
    (near[r.source] = near[r.source] || {})[r.target] = true;
    (near[r.target] = near[r.target] || {})[r.source] = true;
  });
  var pageIndex = {};
  views.forEach(function (v, i) { pageIndex[v.page_id] = i; });
  function occurrencesByView(id) {
    var out = {};
    var e = byId[id];
    (e ? e.occurrences : []).forEach(function (o) {
      if (o.page_id in pageIndex) { out[pageIndex[o.page_id]] = (out[pageIndex[o.page_id]] || 0) + 1; }
    });
    return out;
  }
  var FACET = { identity: '#80ffb7', architecture: '#a6c0ff', experience: '#ff99bd',
                intersection: '#e599ff', base: '#ffffff' };
  var TYPE_FILL = { brand: '#ffd580', product: '#e599ff', organisation: '#80eaff' };
  function swatch(e) {
    if (TYPE_FILL[e.type]) { return TYPE_FILL[e.type]; }
    var f = { purpose: 'identity', content: 'identity', story: 'identity', capability: 'architecture', asset: 'architecture',
              process: 'architecture', task: 'experience', channel: 'experience', journey: 'experience' }[e.type];
    return FACET[f || 'base'];
  }

  // ---- utilities -------------------------------------------------------------------------------------
  function el(tag, attrs, text) {
    var n = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (k) { n.setAttribute(k, attrs[k]); });
    if (text != null) { n.textContent = text; }
    return n;
  }
  var toastTimer = null;
  function toast(msg) {
    var t = $('#toast');
    t.textContent = msg;
    t.classList.add('on');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { t.classList.remove('on'); }, 2200);
  }
  function svgText(i) {
    var tpl = document.getElementById('view-' + i);
    return tpl ? tpl.innerHTML : '';
  }
  function parseBox(s) { return (s || '0 0 100 100').split(/\s+/).map(Number); }
  function easeSpring(t) {                       // critically damped spring, settles at 1
    return 1 - Math.exp(-7 * t) * (1 + 7 * t);
  }
  function settle(promise, ms) {                 // never wait for a frame that a hidden or throttled tab does not paint
    return Promise.race([promise, new Promise(function (r) { setTimeout(r, ms); })]);
  }
  function tween(dur, step) {
    var p = new Promise(function (resolve) {
      if (reduce || dur <= 0) { step(1); resolve(); return; }
      var t0 = null, finished = false;
      function frame(ts) {
        if (finished) { return; }
        if (t0 === null) { t0 = ts; }
        var t = Math.min((ts - t0) / dur, 1);
        step(easeSpring(t));
        if (t < 1) { requestAnimationFrame(frame); } else { finished = true; resolve(); }
      }
      requestAnimationFrame(frame);
      setTimeout(function () { if (!finished) { finished = true; step(1); resolve(); } }, dur + 250);
    });
    return p;
  }

  // ---- state -------------------------------------------------------------------------------------------
  var current = -1;          // -1 = wall
  var svg = null;
  var home = null;           // the view's full viewBox
  var focusId = null;
  var stateMode = 'all';     // all | current | target

  // ---- wall ----------------------------------------------------------------------------------------------
  function buildWall() {
    var wall = $('#wall');
    views.forEach(function (v, i) {
      var card = el('button', { 'class': 'card', type: 'button', 'data-view': String(i),
                                'aria-label': v.name + ' — open view' });
      card.style.setProperty('--i', String(i));
      var thumb = el('div', { 'class': 'thumb' });
      var img = el('img', { alt: '' });
      try {
        img.src = URL.createObjectURL(new Blob([svgText(i)], { type: 'image/svg+xml' }));
      } catch (e) { /* no thumbnail */ }
      thumb.appendChild(img);
      var meta = el('div', { 'class': 'meta' });
      var dots = el('div', { 'class': 'dots', 'aria-hidden': 'true' });
      (v.facets || []).forEach(function (f) {
        var d = el('i');
        d.style.background = FACET[f] || '#ffffff';
        dots.appendChild(d);
      });
      meta.appendChild(dots);
      meta.appendChild(el('h2', null, v.name));
      meta.appendChild(el('p', null, v.elements + ' elements · ' + v.edges + ' relationships'));
      card.appendChild(thumb);
      card.appendChild(meta);
      card.addEventListener('click', function () { openView(i, null, card); });
      wall.appendChild(card);
    });
    var strip = $('#strip');
    views.forEach(function (v, i) {
      var tab = el('button', { 'class': 'tab', type: 'button', 'data-view': String(i) });
      tab.appendChild(el('span', null, v.name));
      tab.appendChild(el('span', { 'class': 'hits' }, ''));
      tab.addEventListener('click', function () { openView(i); });
      strip.appendChild(tab);
    });
  }

  // ---- view --------------------------------------------------------------------------------------------
  function mount(i) {
    var canvas = $('#canvas');
    canvas.textContent = '';
    var holder = document.createElement('div');
    holder.innerHTML = svgText(i);                    // our own renderer's output: sanitised at build time
    svg = holder.querySelector('svg');
    if (!svg) { return; }
    svg.removeAttribute('width');
    svg.removeAttribute('height');
    svg.setAttribute('preserveAspectRatio', 'xMidYMid meet');
    svg.setAttribute('role', 'img');
    svg.setAttribute('aria-label', views[i].name);
    canvas.appendChild(svg);
    home = parseBox(svg.getAttribute('viewBox'));
    $$('g.el', svg).forEach(function (g) {
      var e = byId[g.getAttribute('data-id')];
      g.setAttribute('tabindex', '0');
      g.setAttribute('role', 'button');
      g.setAttribute('aria-label', (e ? e.name + ' — ' + e.type : g.getAttribute('data-type')) + ' ' + g.getAttribute('data-id'));
      g.addEventListener('pointerenter', function () { highlight(g.getAttribute('data-id')); });
      g.addEventListener('pointerleave', function () { highlight(null); });
      g.addEventListener('focus', function () { highlight(g.getAttribute('data-id')); });
      g.addEventListener('blur', function () { highlight(null); });
      g.addEventListener('click', function (ev) { ev.stopPropagation(); inspect(g.getAttribute('data-id')); zoomTo(g); });
      g.addEventListener('keydown', function (ev) {
        if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); inspect(g.getAttribute('data-id')); zoomTo(g); }
      });
    });
    enablePanZoom();
    applyState(false);
  }

  function setChrome() {
    var inView = current >= 0;
    $('#wall').hidden = inView;
    $('#stage').hidden = !inView;
    $('#strip').hidden = !inView;
    $$('.tab').forEach(function (t) {
      if (Number(t.getAttribute('data-view')) === current) { t.setAttribute('aria-current', 'page'); }
      else { t.removeAttribute('aria-current'); }
    });
    var crumb = $('#crumb');
    crumb.textContent = '';
    if (inView) {
      var back = el('button', { type: 'button' }, 'All views');
      back.addEventListener('click', showWall);
      crumb.appendChild(back);
      crumb.appendChild(document.createTextNode(' / ' + views[current].name));
    }
  }

  function openView(i, elementId, fromCard) {
    if (i < 0 || i >= views.length) { return Promise.resolve(); }
    current = i;
    setChrome();
    mount(i);
    inspect(elementId || null);
    updateHash(elementId);
    var paper = $('#paper');
    var anim = Promise.resolve();
    if (fromCard && !reduce && paper.animate) {
      var a = fromCard.getBoundingClientRect();
      var b = paper.getBoundingClientRect();
      if (b.width && b.height) {
        var sx = a.width / b.width, sy = a.height / b.height;
        var player = paper.animate([
          { transform: 'translate(' + (a.left - b.left) + 'px,' + (a.top - b.top) + 'px) scale(' + sx + ',' + sy + ')', opacity: .6 },
          { transform: 'none', opacity: 1 }], { duration: 520, easing: 'cubic-bezier(.2,.8,.2,1)' });
        anim = player.finished ? settle(player.finished.catch(function () {}), 800) : Promise.resolve();
      }
    }
    return anim.then(function () {
      if (elementId) {
        var g = svg && svg.querySelector('g.el[data-id="' + cssEscape(elementId) + '"]');
        if (g) { highlight(elementId); return zoomTo(g); }
      }
    });
  }

  function showWall() {
    var leaving = current;
    current = -1;
    highlight(null);
    setChrome();
    updateHash(null);
    var card = $('.card[data-view="' + leaving + '"]');
    if (card) { card.focus({ preventScroll: false }); }
  }

  function cssEscape(s) { return String(s).replace(/["\\]/g, '\\$&'); }

  // ---- effect 1: zoom (viewBox spring) -----------------------------------------------------------------
  function viewBoxTo(target, dur) {
    if (!svg) { return Promise.resolve(); }
    var from = parseBox(svg.getAttribute('viewBox'));
    var s = svg;
    return tween(dur, function (k) {
      var v = from.map(function (f, n) { return f + (target[n] - f) * k; });
      s.setAttribute('viewBox', v.map(function (x) { return x.toFixed(1); }).join(' '));
    });
  }
  function zoomTo(g) {
    if (!g || !svg) { return Promise.resolve(); }
    var b = g.getBBox();
    var pad = Math.max(b.width, b.height) * 0.9 + 60;
    var w = b.width + pad * 2, h = b.height + pad * 2;
    var rect = svg.getBoundingClientRect();
    var ratio = rect.width && rect.height ? rect.width / rect.height : home[2] / home[3];   // the screen's shape
    if (w / h < ratio) { w = h * ratio; } else { h = w / ratio; }
    if (w > home[2] && h > home[3]) { return resetZoom(); }
    var cx = b.x + b.width / 2, cy = b.y + b.height / 2;
    // keep the frame on the page: never show empty canvas beside the diagram when a closer frame fits
    function clamp(c, size, lo, span) { return size >= span ? lo + span / 2 : Math.min(Math.max(c, lo + size / 2), lo + span - size / 2); }
    cx = clamp(cx, w, home[0], home[2]);
    cy = clamp(cy, h, home[1], home[3]);
    g.classList.remove('pulse');
    void g.getBoundingClientRect();
    g.classList.add('pulse');
    return viewBoxTo([cx - w / 2, cy - h / 2, w, h], 650);
  }
  function resetZoom() { return home ? viewBoxTo(home.slice(), 500) : Promise.resolve(); }

  function enablePanZoom() {
    var s = svg;
    var drag = null;
    s.addEventListener('wheel', function (ev) {
      ev.preventDefault();
      var v = parseBox(s.getAttribute('viewBox'));
      var r = s.getBoundingClientRect();
      var k = Math.exp(ev.deltaY * 0.0015);
      var w = Math.min(Math.max(v[2] * k, home[2] / 12), home[2] * 1.5);
      var h = w * v[3] / v[2];
      var px = v[0] + (ev.clientX - r.left) / r.width * v[2];
      var py = v[1] + (ev.clientY - r.top) / r.height * v[3];
      var nx = px - (px - v[0]) * (w / v[2]), ny = py - (py - v[1]) * (h / v[3]);
      s.setAttribute('viewBox', [nx, ny, w, h].map(function (x) { return x.toFixed(1); }).join(' '));
    }, { passive: false });
    s.addEventListener('pointerdown', function (ev) {
      if (ev.target.closest && ev.target.closest('g.el')) { return; }
      drag = { x: ev.clientX, y: ev.clientY, v: parseBox(s.getAttribute('viewBox')) };
      s.classList.add('panning');
      s.setPointerCapture && s.setPointerCapture(ev.pointerId);
    });
    s.addEventListener('pointermove', function (ev) {
      if (!drag) { return; }
      var r = s.getBoundingClientRect();
      var dx = (ev.clientX - drag.x) / r.width * drag.v[2], dy = (ev.clientY - drag.y) / r.height * drag.v[3];
      s.setAttribute('viewBox', [drag.v[0] - dx, drag.v[1] - dy, drag.v[2], drag.v[3]].map(function (x) { return x.toFixed(1); }).join(' '));
    });
    function end() { drag = null; s.classList.remove('panning'); }
    s.addEventListener('pointerup', end);
    s.addEventListener('pointercancel', end);
    s.addEventListener('dblclick', function () { resetZoom(); });
  }

  // ---- effect 2: cross-view highlight -------------------------------------------------------------------
  function highlight(id) {
    focusId = id;
    if (svg) {
      $$('.is-focus, .is-near, .is-hot', svg).forEach(function (n) { n.classList.remove('is-focus', 'is-near', 'is-hot'); });
      svg.classList.toggle('focusing', !!id);
      if (id) {
        var nb = near[id] || {};
        $$('g.el', svg).forEach(function (g) {
          var gid = g.getAttribute('data-id');
          if (gid === id) { g.classList.add('is-focus'); }
          else if (nb[gid]) { g.classList.add('is-near'); }
        });
        $$('g.deco[data-for]', svg).forEach(function (d) {
          var f = d.getAttribute('data-for');
          if (f === id || nb[f]) { d.classList.add('is-near'); }
        });
        $$('g.edge', svg).forEach(function (e) {
          var s = e.getAttribute('data-src'), t = e.getAttribute('data-tgt');
          if (s === id || t === id) { e.classList.add('is-hot'); }
        });
      }
    }
    var hits = id ? occurrencesByView(id) : {};
    $$('.tab').forEach(function (t) {
      var i = Number(t.getAttribute('data-view'));
      var badge = $('.hits', t);
      var n = hits[i] || 0;
      badge.textContent = n ? String(n) : '';
      badge.classList.toggle('on', n > 0 && i !== current);
    });
  }

  function inspect(id) {
    var box = $('#inspector');
    box.textContent = '';
    var e = id ? byId[id] : null;
    if (!e) {
      box.appendChild(el('p', { 'class': 'empty' }, 'Hover or select an element to see it across every view. ' +
                                                      'Press ⌘K / Ctrl+K to search, T for change annotations, ← → to page.'));
      return;
    }
    box.appendChild(el('h3', null, e.name));
    box.appendChild(el('p', { 'class': 'type' }, e.type + (e.kind ? ' · ' + e.kind : '') + ' · ' + e.id +
                                                 (e.id_source === 'slug' ? ' (no explicit id)' : '')));
    var dl = el('dl');
    function row(k, v) { if (v) { dl.appendChild(el('dt', null, k)); dl.appendChild(el('dd', null, v)); } }
    row('Description', e.description);
    row('Change', e.change);
    Object.keys(e.attributes || {}).forEach(function (k) { row(k, String(e.attributes[k])); });
    if (dl.childNodes.length) { box.appendChild(dl); }
    box.appendChild(el('h4', null, 'Appears in'));
    var ul = el('ul');
    var seen = {};
    e.occurrences.forEach(function (o) {
      var i = pageIndex[o.page_id];
      if (i === undefined || seen[i]) { return; }
      seen[i] = true;
      var li = el('li');
      var b = el('button', { type: 'button' }, views[i].name);
      b.addEventListener('click', function () { openView(i, e.id); });
      li.appendChild(b);
      ul.appendChild(li);
    });
    if (!ul.childNodes.length) { ul.appendChild(el('li', { 'class': 'empty' }, 'only in the model')); }
    box.appendChild(ul);
    var rels = graph.relationships.filter(function (r) { return r.source === e.id || r.target === e.id; });
    if (rels.length) {
      box.appendChild(el('h4', null, 'Relationships'));
      var rl = el('ul');
      rels.slice(0, 40).forEach(function (r) {
        var other = byId[r.source === e.id ? r.target : r.source];
        var li = el('li');
        var text = r.source === e.id ? r.verb + ' → ' : '← ' + r.verb + ' ';
        li.appendChild(document.createTextNode(text));
        var b = el('button', { type: 'button' }, other ? other.name : (r.source === e.id ? r.target : r.source));
        b.addEventListener('click', function () { goTo(other ? other.id : null); });
        li.appendChild(b);
        rl.appendChild(li);
      });
      box.appendChild(rl);
    }
  }

  function goTo(id) {
    var e = id ? byId[id] : null;
    if (!e) { return Promise.resolve(); }
    var here = current >= 0 && svg && svg.querySelector('g.el[data-id="' + cssEscape(id) + '"]');
    if (here) { highlight(id); inspect(id); updateHash(id); return zoomTo(here); }
    var occ = e.occurrences.filter(function (o) { return o.page_id in pageIndex; })[0];
    if (!occ) { toast(e.name + ' is only in the model — not drawn on any view'); inspect(id); return Promise.resolve(); }
    return openView(pageIndex[occ.page_id], id);
  }

  // ---- effect 3: search ------------------------------------------------------------------------------------
  var results = [], sel = 0;
  function openPalette() {
    var p = $('#palette');
    p.hidden = false;
    var input = $('#palette input');
    input.value = '';
    renderResults('');
    input.focus();
  }
  function closePalette() { $('#palette').hidden = true; }
  function renderResults(q) {
    q = q.trim().toLowerCase();
    var list = graph.elements.filter(function (e) {
      return !q || e.name.toLowerCase().indexOf(q) >= 0 || e.id.toLowerCase().indexOf(q) >= 0 ||
             e.type.indexOf(q) === 0 || (e.kind || '').indexOf(q) === 0;
    });
    list.sort(function (a, b) {
      var ap = a.name.toLowerCase().indexOf(q) === 0 ? 0 : 1, bp = b.name.toLowerCase().indexOf(q) === 0 ? 0 : 1;
      return ap - bp || a.name.localeCompare(b.name);
    });
    results = list.slice(0, 50);
    sel = 0;
    var ul = $('#palette ul');
    ul.textContent = '';
    results.forEach(function (e, n) {
      var li = el('li', { role: 'option', 'aria-selected': n === 0 ? 'true' : 'false' });
      var sw = el('span', { 'class': 'sw' });
      sw.style.background = swatch(e);
      li.appendChild(sw);
      li.appendChild(el('span', null, e.name));
      li.appendChild(el('small', null, e.type + (e.kind ? ' · ' + e.kind : '') + ' · ' + e.id));
      li.addEventListener('click', function () { choose(n); });
      ul.appendChild(li);
    });
    if (!results.length) { ul.appendChild(el('li', { 'aria-selected': 'false' }, 'No element matches')); }
  }
  function moveSel(d) {
    if (!results.length) { return; }
    sel = (sel + d + results.length) % results.length;
    $$('#palette li').forEach(function (li, n) { li.setAttribute('aria-selected', n === sel ? 'true' : 'false'); });
    var cur = $$('#palette li')[sel];
    cur && cur.scrollIntoView && cur.scrollIntoView({ block: 'nearest' });
  }
  function choose(n) {
    var e = results[n];
    closePalette();
    return e ? goTo(e.id) : Promise.resolve();
  }

  // ---- effect 4: current ↔ target over change annotations -------------------------------------------------
  function hasChanges() { return !!(svg && svg.querySelector('[data-change]')); }
  function applyState(pulse) {
    if (!svg) { return; }
    svg.classList.toggle('state-current', stateMode === 'current');
    svg.classList.toggle('state-target', stateMode === 'target');
    $$('.decide-mark', svg).forEach(function (n) { n.remove(); });
    if (stateMode !== 'all') {
      $$('g.el[data-change="decide"]', svg).forEach(function (g) {
        var b = g.getBBox();
        var t = document.createElementNS(SVGNS, 'text');
        t.setAttribute('class', 'decide-mark');
        t.setAttribute('x', String(b.x + b.width - 4));
        t.setAttribute('y', String(b.y + 16));
        t.setAttribute('text-anchor', 'end');
        t.setAttribute('font-size', '16');
        t.setAttribute('font-weight', 'bold');
        t.setAttribute('fill', '#bf2600');
        t.textContent = '?';
        g.appendChild(t);
      });
      if (pulse) {
        $$('g.el[data-change="change"], g.el[data-change="replace"]', svg).forEach(function (g) {
          g.classList.remove('pulse'); void g.getBoundingClientRect(); g.classList.add('pulse');
        });
      }
    }
    var btn = $('#btn-state');
    btn.setAttribute('aria-pressed', stateMode === 'all' ? 'false' : 'true');
    $('span', btn).textContent = 'Changes: ' + stateMode;
  }
  function cycleState() {
    if (current < 0) { toast('Open a view first'); return false; }
    if (!hasChanges()) { toast('No change annotations on this page'); return false; }
    stateMode = { all: 'current', current: 'target', target: 'all' }[stateMode];
    applyState(true);
    toast(stateMode === 'current' ? 'Change annotations: current state (new hidden)' :
          stateMode === 'target' ? 'Change annotations: target state (removed hidden)' : 'Change annotations: all');
    updateHash(focusId);
    return true;
  }

  // ---- effect 5: paging, full screen, deep links, print -------------------------------------------------
  function page(d) {
    if (current < 0) { return openView(d > 0 ? 0 : views.length - 1); }
    return openView((current + d + views.length) % views.length);
  }
  function updateHash(id) {
    var h = current < 0 ? '#/' : '#/view/' + views[current].page_id + (id ? '/' + encodeURIComponent(id) : '') +
            (stateMode !== 'all' ? '?state=' + stateMode : '');
    if (location.hash !== h && location.hash !== '#selftest') {
      try { history.replaceState(null, '', h); } catch (e) { /* file:// in some browsers */ }
    }
  }
  function fromHash() {
    var m = /^#\/view\/([a-z0-9-]+)(?:\/([^?]+))?(?:\?state=(current|target))?$/.exec(location.hash || '');
    if (!m || !(m[1] in pageIndex)) { return false; }
    var id = m[2] ? decodeURIComponent(m[2]) : null;
    if (id && !byId[id]) { id = null; }
    if (m[3]) { stateMode = m[3]; }
    openView(pageIndex[m[1]], id);
    return true;
  }
  function buildPrint() {
    var box = $('#print');
    box.textContent = '';
    views.forEach(function (v, i) {
      var sec = el('section');
      sec.appendChild(el('h2', null, v.name));
      var holder = document.createElement('div');
      holder.innerHTML = svgText(i);
      sec.appendChild(holder);
      box.appendChild(sec);
    });
  }

  // ---- theme -------------------------------------------------------------------------------------------------
  function setTheme(t) {
    document.documentElement.setAttribute('data-theme', t);
    try { localStorage.setItem('edgy-presenter-theme', t); } catch (e) { /* private window */ }
  }
  function toggleTheme() {
    var t = document.documentElement.getAttribute('data-theme');
    var dark = t ? t === 'dark' : (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches);
    setTheme(dark ? 'light' : 'dark');
  }

  // ---- keys --------------------------------------------------------------------------------------------------
  document.addEventListener('keydown', function (ev) {
    var palette = !$('#palette').hidden;
    if ((ev.metaKey || ev.ctrlKey) && ev.key.toLowerCase() === 'k') { ev.preventDefault(); palette ? closePalette() : openPalette(); return; }
    if (palette) {
      if (ev.key === 'Escape') { closePalette(); }
      else if (ev.key === 'ArrowDown') { ev.preventDefault(); moveSel(1); }
      else if (ev.key === 'ArrowUp') { ev.preventDefault(); moveSel(-1); }
      else if (ev.key === 'Enter') { ev.preventDefault(); choose(sel); }
      return;
    }
    if (ev.target && /input|textarea/i.test(ev.target.tagName)) { return; }
    if (ev.key === 'ArrowRight' || ev.key === 'PageDown') { ev.preventDefault(); page(1); }
    else if (ev.key === 'ArrowLeft' || ev.key === 'PageUp') { ev.preventDefault(); page(-1); }
    else if (ev.key === 'Escape') { if (current >= 0) { showWall(); } }
    else if (ev.key === 't' || ev.key === 'T') { cycleState(); }
    else if (ev.key === 'f' || ev.key === 'F') {
      var d = document.documentElement;
      if (document.fullscreenElement) { document.exitFullscreen(); } else if (d.requestFullscreen) { d.requestFullscreen(); }
    }
    else if (ev.key === '0') { resetZoom(); }
    else if (ev.key === '/') { ev.preventDefault(); openPalette(); }
  });

  // ---- boot ----------------------------------------------------------------------------------------------------
  try {
    var t = localStorage.getItem('edgy-presenter-theme');
    if (t === 'dark' || t === 'light') { document.documentElement.setAttribute('data-theme', t); }
  } catch (e) { /* storage unavailable */ }
  buildWall();
  setChrome();
  inspect(null);
  $('#btn-search').addEventListener('click', openPalette);
  $('#btn-state').addEventListener('click', cycleState);
  $('#btn-theme').addEventListener('click', toggleTheme);
  $('#btn-full').addEventListener('click', function () {
    var d = document.documentElement;
    if (document.fullscreenElement) { document.exitFullscreen(); } else if (d.requestFullscreen) { d.requestFullscreen(); }
  });
  $('#palette').addEventListener('click', function (ev) { if (ev.target === $('#palette')) { closePalette(); } });
  $('#palette input').addEventListener('input', function (ev) { renderResults(ev.target.value); });
  window.addEventListener('beforeprint', buildPrint);
  window.addEventListener('hashchange', function () { if (location.hash !== '#selftest') { fromHash(); } });
  if (location.hash === '#selftest') { selftest(); } else { fromHash(); }

  // ---- self-test (CI: headless Chrome --dump-dom file://…#selftest) ------------------------------------------
  function selftest() {
    var steps = [];
    function check(name, ok) { steps.push(name + ':' + (ok ? 'ok' : 'FAIL')); if (!ok) { throw new Error(name); } }
    var done = function (ok) {
      var s = el('div', { id: 'edgy-selftest', 'data-result': ok ? 'pass' : 'fail',
                          'data-errors': String(errors), 'data-steps': steps.join(' ') });
      document.body.appendChild(s);
    };
    var pick = null;
    Promise.resolve().then(function () {
      check('wall', $$('.card').length === views.length && views.length > 0);
      // a card is never flattened: its 16:10 thumbnail and title stay whole (row sizing bug seen on phones)
      check('wall-cards', $$('.card').every(function (c) { return c.offsetHeight >= c.offsetWidth * 0.62; }));
      return openView(0, null, $('.card'));
    }).then(function () {
      check('view', !!svg && current === 0);
      var before = svg.getAttribute('viewBox');
      pick = svg.querySelector('g.el[data-id]');
      check('elements', !!pick);
      highlight(pick.getAttribute('data-id'));
      check('highlight', svg.classList.contains('focusing') && pick.classList.contains('is-focus'));
      return zoomTo(pick).then(function () { check('zoom', svg.getAttribute('viewBox') !== before); });
    }).then(function () {
      highlight(null);
      openPalette();
      var e = byId[pick.getAttribute('data-id')];
      var input = $('#palette input');
      input.value = e ? e.name : '';
      renderResults(input.value);
      check('search', results.length > 0 && results[0].name === (e && e.name));
      return choose(0);
    }).then(function () {
      check('search-jump', $('#palette').hidden && !!svg.querySelector('g.el.is-focus'));
      var withChanges = views.map(function (v, i) { return i; }).filter(function (i) { return /data-change=/.test(svgText(i)); })[0];
      var noChanges = views.map(function (v, i) { return i; }).filter(function (i) { return !/data-change=/.test(svgText(i)); })[0];
      var chain = Promise.resolve();
      if (noChanges !== undefined) {
        chain = chain.then(function () { return openView(noChanges); }).then(function () {
          var before = stateMode;
          check('state-noop', cycleState() === false && stateMode === before);
        });
      }
      if (withChanges !== undefined) {
        chain = chain.then(function () { return openView(withChanges); }).then(function () {
          check('state-current', cycleState() && svg.classList.contains('state-current'));
          check('state-target', cycleState() && svg.classList.contains('state-target'));
          cycleState();
        });
      }
      return chain;
    }).then(function () {
      var before = current;
      return page(1).then(function () { check('paging', views.length < 2 || current === (before + 1) % views.length); });
    }).then(function () {
      showWall();
      check('back', current === -1 && !$('#wall').hidden);
      check('no-errors', errors === 0);
      done(true);
    }).catch(function () { done(false); });
  }
})();

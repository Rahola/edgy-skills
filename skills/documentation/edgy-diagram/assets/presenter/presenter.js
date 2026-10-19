/* EDGY presenter-lite (edgy-diagram 2.9.0, extension contract 1).
 * Five effects, no more (a sixth goes to F6b): card wall → zoom, cross-view highlight,
 * search, current ↔ target filter over change annotations, paging. Drill-through on a
 * realisation trace belongs to effect 5 (paging and deep links): no new effect. No network,
 * no eval, text only through textContent. Every animation is a cut with prefers-reduced-motion. */
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
  // model ids are data: every index is a null-prototype object, so an id such as "constructor" or
  // "__proto__" is an inert key and never reaches Object.prototype
  function dict() { return Object.create(null); }
  var byId = dict();
  graph.elements.forEach(function (e) { byId[e.id] = e; });
  var near = dict();
  graph.relationships.forEach(function (r) {
    (near[r.source] = near[r.source] || dict())[r.target] = true;
    (near[r.target] = near[r.target] || dict())[r.source] = true;
  });
  var pageIndex = dict();
  views.forEach(function (v, i) { pageIndex[v.page_id] = i; });
  // realisation trace (2.9.0): one Trace card (the index); element pages and list pages are reached by drilling
  var traceIndex, traceOf = dict(), listOf = dict(), visible = [];
  views.forEach(function (v, i) {
    if (v.trace === 'index' && traceIndex === undefined) { traceIndex = i; }
    else if (v.trace === 'page' && v.focus && !Object.prototype.hasOwnProperty.call(traceOf, v.focus)) { traceOf[v.focus] = i; }
    else if (v.trace === 'list' && v.focus) { listOf[v.focus + '\n' + v.band] = i; }
    if (v.trace !== 'page' && v.trace !== 'list') { visible.push(i); }
  });
  function has(o, k) { return Object.prototype.hasOwnProperty.call(o, k); }
  function occurrencesByView(id) {
    var out = dict();
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
  var inspectedId = null;
  var focusId = null;
  var stateMode = 'all';     // all | current | target
  var selectedId = null;     // the card inspected by the first click; a second click drills through
  var tracePath = [];        // the trace path taken: element ids, the last one is the open trace page
  var traceBand = null;      // above | below on a list page
  var lastHash = null;       // the route this page last showed (popstate and hashchange both arrive)
  var navPromise = Promise.resolve();
  // Composition navigation contract 1: local history also works in about:srcdoc,
  // where browser History may reject opaque file origins. This is not a new effect.
  var localRoutes = ['#/'], localPrevious = [null], localAt = 0, restoring = false;
  var browserHistory = true;
  // A route string cannot identify a history entry: A → B → A has two different
  // positions. Retain entry identities/predecessors, even when a branch changes.
  var historySession = String(Date.now()) + ':' + String(Math.random());
  function historyState(at) {
    var out = dict(), state = history.state;
    if (state && typeof state === 'object' && !Array.isArray(state)) {
      Object.keys(state).forEach(function (key) { out[key] = state[key]; });
    }
    out.edgyNavigation = { session: historySession, index: at };
    return out;
  }
  function historyPosition(h) {
    try {
      var state = history.state, marker = state && state.edgyNavigation;
      if (marker && marker.session === historySession && Number.isInteger(marker.index) &&
          marker.index >= 0 && marker.index < localRoutes.length &&
          localRoutes[marker.index] === (h === '' || h === '#' ? '#/' : h)) {
        return marker.index;
      }
    } catch (e) { /* opaque srcdoc: the local predecessor chain remains usable */ }
    return null;
  }
  function writeRoute(h, push) {
    lastHash = h;
    var previousAt = localAt;
    if (!restoring && localRoutes[localAt] !== h) {
      localPrevious.push(localAt);
      localRoutes.push(h); localAt = localRoutes.length - 1;
    }
    try {
      if (push && location.hash !== h) {
        // Also label the initial entry (whose URL may have no fragment). Preserve
        // unrelated host state; a reload's old session marker is never trusted.
        history.replaceState(historyState(previousAt), '', location.href);
        history.pushState(historyState(localAt), '', h);
      } else { history.replaceState(historyState(localAt), '', h); }
    } catch (e) { browserHistory = false; }
  }

  // ---- wall ----------------------------------------------------------------------------------------------
  function buildWall() {
    var wall = $('#wall');
    visible.forEach(function (i) {
      var v = views[i];
      var card = el('button', { 'class': 'card', type: 'button', 'data-view': String(i) });
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
    visible.forEach(function (i) {
      var v = views[i];
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
    svg.setAttribute('role', 'group');
    svg.setAttribute('aria-label', views[i].name);
    canvas.appendChild(svg);
    home = parseBox(svg.getAttribute('viewBox'));
    $$('g.el', svg).forEach(function (g) {
      var e = byId[g.getAttribute('data-id')];
      g.setAttribute('tabindex', '0');
      g.setAttribute('role', 'button');
      g.setAttribute('aria-label', g.textContent.replace(/\s+/g, ' ').trim() + ' — ' + (e ? e.type : g.getAttribute('data-type')) + ' ' + g.getAttribute('data-id'));
      g.addEventListener('pointerenter', function () { highlight(g.getAttribute('data-id')); });
      g.addEventListener('pointerleave', function () { highlight(null); });
      g.addEventListener('focus', function () { highlight(g.getAttribute('data-id')); });
      g.addEventListener('blur', function () { highlight(null); });
      g.addEventListener('click', function (ev) { ev.stopPropagation(); select(g); });
      g.addEventListener('keydown', function (ev) {
        if (ev.target === g && (ev.key === 'Enter' || ev.key === ' ')) { ev.preventDefault(); select(g); }
      });
      if (linkOf(g) !== null) { addDrillBadge(g, e); }
    });
    $$('g.deco[data-link]', svg).forEach(function (d) {      // "+N more" → list page; "C4" badge → C4 page
      if (!has(pageIndex, d.getAttribute('data-link'))) { return; }
      var to = views[pageIndex[d.getAttribute('data-link')]];
      d.setAttribute('tabindex', '0');
      d.setAttribute('role', 'link');
      d.setAttribute('aria-label', d.textContent.trim() + ' — ' + (to.trace === 'list' ? 'Show every card of this band' : 'Open ' + to.name));
      d.classList.add('linked');
      addHitArea(d);
      function go() { openLink(d.getAttribute('data-link')); }
      d.addEventListener('click', function (ev) { ev.stopPropagation(); go(); });
      d.addEventListener('keydown', function (ev) { if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); go(); } });
    });
    selectedId = null;
    enablePanZoom();
    applyState(false);
  }

  // ---- drill-through (effect 5): the "→" badge or a second click opens a card's trace page ---------------------
  function linkOf(g) {
    var l = g.getAttribute('data-link');
    return l && has(pageIndex, l) && views[pageIndex[l]].trace === 'page' ? l : null;
  }
  function cssUnit() {                                    // SVG units per CSS pixel at the view's full size
    var w = svg && svg.getBoundingClientRect().width;
    return w && home ? Math.max(1, home[2] / w) : 1;
  }
  function addHitArea(d) {                                // a small link (the C4 badge) gets a 24 px target
    var b = d.getBBox(), u = cssUnit(), w = Math.max(b.width, 24 * u), h = Math.max(b.height, 24 * u);
    if (w === b.width && h === b.height) { return; }
    var hit = document.createElementNS(SVGNS, 'rect');
    hit.setAttribute('x', String(b.x + b.width / 2 - w / 2));
    hit.setAttribute('y', String(b.y + b.height / 2 - h / 2));
    hit.setAttribute('width', String(w));
    hit.setAttribute('height', String(h));
    hit.setAttribute('fill', 'transparent');
    hit.setAttribute('class', 'hit');
    d.appendChild(hit);
  }
  function addDrillBadge(g, e) {
    var b = g.getBBox();
    var badge = document.createElementNS(SVGNS, 'g');
    badge.setAttribute('class', 'drill');
    badge.setAttribute('data-drill-for', g.getAttribute('data-id'));
    badge.setAttribute('tabindex', '0');
    badge.setAttribute('role', 'link');
    badge.setAttribute('aria-label', 'Open the trace of ' + (e ? e.name : g.getAttribute('data-id')));
    var r = Math.max(11, 12 * cssUnit());                // at least 24 CSS px across, also on a phone
    var c = document.createElementNS(SVGNS, 'circle');
    c.setAttribute('cx', String(b.x + b.width - 2));
    c.setAttribute('cy', String(b.y + 2));
    c.setAttribute('r', String(r));
    var t = document.createElementNS(SVGNS, 'text');
    t.setAttribute('x', String(b.x + b.width - 2));
    t.setAttribute('y', String(b.y + 2 + r * 0.45));
    t.setAttribute('text-anchor', 'middle');
    t.setAttribute('font-size', String(r * 1.25));
    t.setAttribute('font-weight', 'bold');
    t.textContent = '→';
    badge.appendChild(c);
    badge.appendChild(t);
    function go(ev) { ev.preventDefault(); ev.stopPropagation(); drill(g.getAttribute('data-id')); }
    badge.addEventListener('click', go);
    badge.addEventListener('keydown', function (ev) { if (ev.key === 'Enter' || ev.key === ' ') { go(ev); } });
    // Separate controls: a focusable link must not be nested in the card button.
    g.parentNode.insertBefore(badge, g.nextSibling);
    g.classList.add('linked');
  }
  function select(g) {
    var id = g.getAttribute('data-id');
    if (selectedId === id && linkOf(g) !== null) { drill(id); return; }
    selectedId = id;
    inspect(id);
    zoomTo(g);
  }
  function traceHash(path, band) {
    return '#/trace' + path.map(function (p) { return '/' + encodeURIComponent(p); }).join('') + (band ? '/+' + band : '') +
      (stateMode !== 'all' ? '?state=' + stateMode : '');
  }
  function drill(id) {
    if (!has(traceOf, id)) { toast('No trace page for ' + id); return navPromise; }
    var base = current >= 0 && views[current].trace && views[current].trace !== 'index' ? tracePath : [];
    var at = base.indexOf(id);
    return goTrace(at >= 0 ? base.slice(0, at + 1) : base.concat([id]), null, true);
  }
  function openLink(pid) {
    var v = views[pageIndex[pid]];
    if (!v) { return navPromise; }
    if (v.trace === 'list') {
      var path = tracePath.length && tracePath[tracePath.length - 1] === v.focus ? tracePath : [v.focus];
      return goTrace(path, v.band, true);
    }
    if (v.trace === 'page') { return drill(v.focus); }
    // another page (the C4 badge, Q3): a history entry of its own, so back returns to the trace
    var h = '#/view/' + pid;
    writeRoute(h, true);
    navPromise = openView(pageIndex[pid]);
    return navPromise;
  }
  function traceTarget(path, band) {
    if (!path.length) { return band ? undefined : traceIndex; }
    var last = path[path.length - 1];
    return band ? listOf[last + '\n' + band] : (has(traceOf, last) ? traceOf[last] : undefined);
  }
  function goTrace(path, band, push) {
    var i = traceTarget(path, band || null);
    if (i === undefined) { toast('Not found in this presentation'); return navPromise; }
    tracePath = path.slice();
    traceBand = band || null;
    var h = traceHash(tracePath, traceBand);
    writeRoute(h, push);
    navPromise = openView(i, null, null, true);
    if (path.length) { inspect(path[path.length - 1]); }
    return navPromise;
  }
  function parseTrace(h) {
    var m = /^#\/trace((?:\/[^/?#]*)*)(?:\?state=(current|target))?$/.exec(h);
    if (!m) { return null; }
    var segs = m[1] ? m[1].split('/').slice(1) : [];
    var band = null;
    if (segs.length && /^\+(above|below)$/.test(segs[segs.length - 1])) { band = segs.pop().slice(1); }
    var path = [];
    for (var n = 0; n < segs.length; n++) {
      var id;
      try { id = decodeURIComponent(segs[n]); } catch (e) { return null; }
      if (!validModelId(id) || !has(traceOf, id)) { return null; }
      path.push(id);
    }
    return traceTarget(path, band) === undefined ? null : { path: path, band: band, state: m[2] || 'all' };
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
      var v = views[current];
      if (v.trace && traceIndex !== undefined && v.trace !== 'index') {
        // the path taken: Trace / journey / task / …, each crumb jumps back to its page
        var home = el('button', { type: 'button', 'data-depth': '0' }, views[traceIndex].name);
        home.addEventListener('click', function () { goTrace([], null, true); });
        crumb.appendChild(document.createTextNode(' / '));
        crumb.appendChild(home);
        tracePath.forEach(function (id, n) {
          var name = byId[id] ? byId[id].name : id;
          crumb.appendChild(document.createTextNode(' / '));
          if (n === tracePath.length - 1 && !traceBand) { crumb.appendChild(el('span', { 'aria-current': 'page' }, name)); return; }
          var b = el('button', { type: 'button', 'data-depth': String(n + 1) }, name);
          b.addEventListener('click', function () { goTrace(tracePath.slice(0, n + 1), null, true); });
          crumb.appendChild(b);
        });
        if (traceBand) { crumb.appendChild(document.createTextNode(' / ' + v.name)); }
      } else {
        crumb.appendChild(document.createTextNode(' / ' + v.name));
      }
    }
  }

  function openView(i, elementId, fromCard, routed) {
    if (i < 0 || i >= views.length) { return Promise.resolve(); }
    current = i;
    if (!routed) { syncTrace(i); }
    setChrome();
    mount(i);
    focusId = null;
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

  function syncTrace(i) {                          // a trace page opened by a tab, search or paging: a path of one
    var v = views[i];
    if (!v.trace) { return; }
    if (v.trace === 'index') { tracePath = []; traceBand = null; return; }
    if (tracePath[tracePath.length - 1] !== v.focus || traceBand !== (v.band || null)) {
      tracePath = [v.focus];
      traceBand = v.band || null;
    }
  }

  function showWall() {
    var leaving = current;
    current = -1;
    highlight(null);
    setChrome();
    updateHash(null);
    var card = $('.card[data-view="' + leaving + '"]') || (traceIndex !== undefined && $('.card[data-view="' + traceIndex + '"]'));
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
      // cards, drill badges and linked decorations ("+N more", the C4 badge, C4 page links) keep their click:
      // capturing the pointer for panning would retarget it to the <svg>
      if (ev.target.closest && ev.target.closest('g.el, g.drill, g.deco.linked')) { return; }
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
        var nb = near[id] || dict();
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
    var hits = id ? occurrencesByView(id) : dict();
    $$('.tab').forEach(function (t) {
      var i = Number(t.getAttribute('data-view'));
      var badge = $('.hits', t);
      var n = hits[i] || 0;
      badge.textContent = n ? String(n) : '';
      badge.classList.toggle('on', n > 0 && i !== current);
    });
  }

  function inspect(id) {
    inspectedId = id && has(byId, id) ? id : null;
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
    var seen = dict();
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

  function goTo(id, push) {
    var e = id ? byId[id] : null;
    if (!e) { return Promise.resolve(); }
    var here = current >= 0 && svg && svg.querySelector('g.el[data-id="' + cssEscape(id) + '"]');
    if (here) { if (push) { writeRoute(viewRoute(current, id), true); } highlight(id); inspect(id); updateHash(id); return zoomTo(here); }
    var occs = e.occurrences.filter(function (o) { return o.page_id in pageIndex; });
    var occ = occs.filter(function (o) { return !views[pageIndex[o.page_id]].trace; })[0] ||
              (has(traceOf, id) ? { page_id: views[traceOf[id]].page_id } : occs[0]);
    if (!occ) { toast(e.name + ' is only in the model — not drawn on any view'); inspect(id); return Promise.resolve(); }
    if (push) { writeRoute(viewRoute(pageIndex[occ.page_id], id), true); }
    return openView(pageIndex[occ.page_id], id);
  }

  // ---- effect 3: search ------------------------------------------------------------------------------------
  var results = [], sel = 0;
  var paletteOpener = null;
  function openPalette() {
    var p = $('#palette');
    paletteOpener = document.activeElement;
    p.hidden = false;
    p.showModal();
    var input = $('#palette input');
    input.value = '';
    renderResults('');
    input.focus();
  }
  function closePalette() { var p = $('#palette'); p.close(); p.hidden = true; if (paletteOpener && paletteOpener.isConnected) { paletteOpener.focus(); } }
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
      var li = el('li', { id: 'edgy-option-' + n, role: 'option', 'aria-selected': n === 0 ? 'true' : 'false' });
      var sw = el('span', { 'class': 'sw' });
      sw.style.background = swatch(e);
      li.appendChild(sw);
      li.appendChild(el('span', null, e.name));
      li.appendChild(el('small', null, e.type + (e.kind ? ' · ' + e.kind : '') + ' · ' + e.id));
      li.addEventListener('click', function () { choose(n); });
      ul.appendChild(li);
    });
    if (results.length) { $('#palette input').setAttribute('aria-activedescendant', 'edgy-option-0'); }
    else { $('#palette input').removeAttribute('aria-activedescendant'); }
    if (!results.length) { ul.appendChild(el('li', { role: 'option', 'aria-disabled': 'true', 'aria-selected': 'false' }, 'No element matches')); }
  }
  function moveSel(d) {
    if (!results.length) { return; }
    sel = (sel + d + results.length) % results.length;
    $$('#palette li').forEach(function (li, n) { li.setAttribute('aria-selected', n === sel ? 'true' : 'false'); });
    $('#palette input').setAttribute('aria-activedescendant', 'edgy-option-' + sel);
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
    if (!visible.length) { return Promise.resolve(); }
    if (current < 0) { return openView(visible[d > 0 ? 0 : visible.length - 1]); }
    var at = visible.indexOf(current);
    if (at < 0) { at = visible.indexOf(traceIndex); }             // from a trace page: page on from the Trace card
    return openView(visible[(at + d + visible.length) % visible.length]);
  }
  function viewRoute(i, id) {
    if (i < 0) { return '#/'; }
    return views[i].trace && !id ? traceHash(tracePath, traceBand) :
      '#/view/' + views[i].page_id + (id ? '/' + encodeURIComponent(id) : '') +
      (stateMode !== 'all' ? '?state=' + stateMode : '');
  }
  function updateHash(id) {
    if (location.hash !== '#selftest') { writeRoute(viewRoute(current, id), false); }
  }
  function validModelId(id) { return typeof id === 'string' && /^[A-Za-z0-9][A-Za-z0-9._:/-]*$/.test(id) && !/\s/.test(id); }
  function route(h, push) {
    if (typeof h !== 'string' || /\s/.test(h)) { return false; }
    // false (with a "not found" toast) for anything that is not a page of this file: the view stays as it is
    if (/^#\/trace(?:\/|\?|$)/.test(h)) {
      var t = parseTrace(h);
      if (!t) { toast('Not found in this presentation'); return false; }
      stateMode = t.state;
      goTrace(t.path, t.band, !!push);
      return true;
    }
    var m = /^#\/view\/([a-z0-9-]+)(?:\/([^?]+))?(?:\?state=(current|target))?$/.exec(h);
    if (!m || !has(pageIndex, m[1])) {
      if (/^#\/view/.test(h)) { toast('Not found in this presentation'); }
      return false;
    }
    var id = null;
    try { id = m[2] ? decodeURIComponent(m[2]) : null; } catch (e) { return false; }
    if (id && (!validModelId(id) || !has(byId, id) || !(byId[id].occurrences || []).some(function (o) { return o.page_id === m[1]; }))) { return false; }
    stateMode = m[3] || 'all';
    if (views[pageIndex[m[1]]].trace && !id) {
      syncTrace(pageIndex[m[1]]);
      goTrace(tracePath, traceBand, !!push);
      return true;
    }
    if (push) { writeRoute(viewRoute(pageIndex[m[1]], id), true); }
    navPromise = openView(pageIndex[m[1]], id);
    return true;
  }
  // Public composition API. Commands accept data only, never selectors, HTML or URLs.
  // Await frame load (API exists) and .ready before reading initial state.
  var commands = Promise.resolve();
  function command(fn) {
    var next = commands.then(fn);
    commands = next.catch(function () {});
    return next;
  }
  function state() {
    return { contract: 1, route: localRoutes[localAt],
      pageId: current < 0 ? null : views[current].page_id,
      elementId: current < 0 ? null : (inspectedId || views[current].focus || null),
      canGoBack: localPrevious[localAt] !== null, history: browserHistory ? 'browser' : 'local' };
  }
  function navigate(h, push) {
    if (typeof h !== 'string') { return Promise.resolve(false); }
    if (h === '#/') { if (push) { writeRoute(h, true); } showWall(); return Promise.resolve(true); }
    if (!route(h, push)) { return Promise.resolve(false); }
    return navPromise.then(function () { return true; });
  }
  var publicAPI = {
    contract: 1,
    openElement: function (id) {
      return command(function () {
        if (!validModelId(id) || !has(byId, id) || byId[id].id_source === 'slug') { return false; }
        if (has(traceOf, id)) { return goTrace([id], null, true).then(function () { return true; }); }
        if (!(byId[id].occurrences || []).some(function (o) { return has(pageIndex, o.page_id); })) { return false; }
        return goTo(id, true).then(function () { return true; });
      });
    },
    navigate: function (h) { return command(function () { return navigate(h, true); }); },
    back: function () {
      return command(function () {
        if (localPrevious[localAt] === null) { return false; }
        localAt = localPrevious[localAt]; restoring = true;
        return navigate(localRoutes[localAt]).finally(function () { restoring = false; });
      });
    },
    getState: state,
    ready: null
  };

  function fromHash() { return route(location.hash || ''); }
  function onNav() {                                   // back / forward / an edited address: show that route
    var h = location.hash || '';
    if (h === '#selftest') { return; }
    var position = historyPosition(h);
    if (position !== null) { localAt = position; }
    if (h === lastHash) { return; }
    lastHash = h;
    var wasRestoring = restoring;
    restoring = position !== null || wasRestoring;
    try {
      if (h === '' || h === '#/' || h === '#') { showWall(); }
      else { fromHash(); }
    } finally { restoring = wasRestoring; }
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
      if (ev.key === 'Escape') { ev.preventDefault(); closePalette(); }
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
  $('#palette').addEventListener('cancel', function (ev) { ev.preventDefault(); closePalette(); });
  $('#palette').addEventListener('click', function (ev) { if (ev.target === $('#palette')) { closePalette(); } });
  $('#palette input').addEventListener('input', function (ev) { renderResults(ev.target.value); });
  window.addEventListener('beforeprint', buildPrint);
  window.addEventListener('hashchange', onNav);
  window.addEventListener('popstate', onNav);
  var cspViolations = 0;
  document.addEventListener('securitypolicyviolation', function () { cspViolations += 1; });
  if (location.hash === '#selftest') { selftest(); }
  else {
    lastHash = location.hash;
    var start = location.hash || document.documentElement.getAttribute('data-edgy-start') || '';
    if (start) { route(start); }
  }
  commands = navPromise;
  publicAPI.ready = navPromise.then(state);
  window.EDGY_PRESENT = Object.freeze(publicAPI);

  // ---- self-test (CI: headless Chrome --dump-dom file://…#selftest) ------------------------------------------
  function waitNav(ms) {                              // the next back / forward / hash route, or the time-out
    return new Promise(function (resolve) {
      var t = setTimeout(done, ms);
      function done() {
        clearTimeout(t);
        window.removeEventListener('popstate', later);
        window.removeEventListener('hashchange', later);
        resolve(navPromise);
      }
      function later() { setTimeout(done, 0); }
      window.addEventListener('popstate', later);
      window.addEventListener('hashchange', later);
    });
  }
  function traceSteps(check) {
    if (traceIndex === undefined) { return Promise.resolve(); }
    var a = null, b = null;
    function focusIs(id, depth) { return views[current].trace === 'page' && views[current].focus === id && tracePath.length === depth; }
    return goTrace([], null, true).then(function () {
      check('trace-card', current === traceIndex && $$('.card[data-view="' + traceIndex + '"]').length === 1);
      var g = $$('g.el.linked', svg)[0];
      a = g && g.getAttribute('data-id');
      svg.querySelector('g.drill[data-drill-for="' + cssEscape(a) + '"]').dispatchEvent(new MouseEvent('click', { bubbles: true }));
      return navPromise;
    }).then(function () {
      check('drill', focusIs(a, 1) && location.hash === traceHash([a], null));
      var g = $$('g.el.linked', svg).filter(function (n) { return n.getAttribute('data-id') !== a; })[0];
      b = g && g.getAttribute('data-id');
      var before = current;
      g.dispatchEvent(new MouseEvent('click', { bubbles: true }));
      check('card-first-click', current === before && selectedId === b);
      g.dispatchEvent(new MouseEvent('click', { bubbles: true }));
      return navPromise;
    }).then(function () {
      check('card-second-click', focusIs(b, 2));
      var crumb = $('#crumb button[data-depth="1"]');
      check('breadcrumb', !!crumb && $$('#crumb button[data-depth]').length === 2 && !!$('#crumb [aria-current="page"]'));
      crumb.click();
      return navPromise;
    }).then(function () {
      check('breadcrumb-jump', focusIs(a, 1));
      var p = waitNav(2000);
      history.back();
      return p;
    }).then(function () {
      check('history-back', focusIs(b, 2));
      var p = waitNav(2000);
      history.forward();
      return p;
    }).then(function () {
      check('forward', focusIs(a, 1));
      var p = waitNav(2000);
      location.hash = traceHash([a, b], null);
      return p;
    }).then(function () {
      check('deeplink-restore', focusIs(b, 2) && $$('#crumb button[data-depth]').length === 2);
      var before = current;
      var bad = ['#/trace/%E0%A4%A', '#/trace/NOPE', '#/trace/..%2F..', '#/view/', '#/trace/+below/x', '#/trace//'];
      check('route-malformed', bad.every(function (h) { return route(h) === false && current === before; }) &&
                               $('#toast').textContent === 'Not found in this presentation' && cspViolations === 0);
      // Q3: on a trace page with a "C4" badge, the card drills and the badge opens the C4 page; back returns
      var withBadge = views.filter(function (v) {
        return v.trace === 'page' && /<g class="deco"[^>]*data-link="(?!trace-)/.test(svgText(v.index));
      })[0];
      if (!withBadge) { return null; }
      return goTrace([withBadge.focus], null, true).then(function () {
        var badge = $$('g.deco[data-link]', svg).filter(function (d) {
          return !views[pageIndex[d.getAttribute('data-link')]].trace;
        })[0];
        var target = pageIndex[badge.getAttribute('data-link')];
        // the pointer sequence a mouse sends: a pan must not capture it (a synthetic click alone hid that bug)
        var r = badge.getBoundingClientRect();
        var at = { bubbles: true, cancelable: true, clientX: r.left + r.width / 2, clientY: r.top + r.height / 2,
                   pointerId: 1, pointerType: 'mouse', isPrimary: true, button: 0 };
        badge.dispatchEvent(new PointerEvent('pointerdown', at));
        check('badge-no-pan', !svg.classList.contains('panning'));
        badge.dispatchEvent(new PointerEvent('pointerup', at));
        badge.dispatchEvent(new MouseEvent('click', at));
        return navPromise.then(function () { return target; });
      }).then(function (target) {
        check('card-vs-badge', current === target && !views[current].trace);
        var p = waitNav(2000);
        history.back();
        return p;
      }).then(function () {
        check('return-to-trace', views[current].trace === 'page' && views[current].focus === withBadge.focus);
      });
    });
  }

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
      check('wall', $$('.card').length === visible.length && visible.length > 0);
      // a card is never flattened: its 16:10 thumbnail and title stay whole (row sizing bug seen on phones)
      check('wall-cards', $$('.card').every(function (c) { return c.offsetHeight >= c.offsetWidth * 0.62; }));
      return openView(visible[0], null, $('.card'));
    }).then(function () {
      check('view', !!svg && current === visible[0]);
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
      return page(1).then(function () {
        check('paging', visible.length < 2 || current === visible[(visible.indexOf(before) + 1) % visible.length]);
      });
    }).then(function () {
      return traceSteps(check);
    }).then(function () {
      showWall();
      check('back', current === -1 && !$('#wall').hidden);
      check('inert-keys', !Object.prototype.hasOwnProperty.call(Object, 'CAP-X') && ({}).constructor === Object &&
                          Object.getPrototypeOf(byId) === null && Object.getPrototypeOf(near) === null);
      check('no-errors', errors === 0 && cspViolations === 0);
      done(true);
    }).catch(function () { done(false); });
  }
})();

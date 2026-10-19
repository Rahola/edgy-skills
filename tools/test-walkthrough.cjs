#!/usr/bin/env node
/* Optional repository browser tests. Runtime skills remain stdlib/offline.
 * npm install playwright @axe-core/playwright; EDGY_CHROMIUM=<Chrome> node tools/test-walkthrough.cjs
 * NODE_PATH may point to a separate dependency directory. See docs/testing/v2.6.0-browser.md.
 */
'use strict';
const fs = require('fs'), path = require('path'), os = require('os'), http = require('http');
const {spawnSync} = require('child_process');
const {chromium} = require('playwright');
const AxeBuilder = require('@axe-core/playwright').default;
const assert = require('assert/strict');
const root = path.resolve(__dirname, '..');
const work = fs.mkdtempSync(path.join(os.tmpdir(), 'edgy-composition-test-'));
const reportDir = process.env.EDGY_TEST_OUT || work;
fs.mkdirSync(reportDir, {recursive:true});
const results = [], errors = [], network = [], csp = [];
const demo = path.join(root,'docs/examples/executive-walkthrough/index.html');
const exe = process.env.EDGY_CHROMIUM || ['/usr/bin/google-chrome','/usr/bin/chromium','/usr/bin/chromium-browser'].find(fs.existsSync);
const py = spawnSync(process.env.PYTHON || 'python3', ['-c', `import sys,json,os
sys.path.insert(0,'skills/documentation/edgy-diagram/scripts')
import test_present,edgy_present
from pathlib import Path
h,st,out,drawio=test_present._build()
pages=test_present.DEMO.split('  - name: "Trace"')[0]
plain,_,_,_=test_present._build(pages)
# A fixture with a model-only id and an intentionally slug-only id.
graph=json.loads(__import__('re').search(r'id="edgy-graph">(.*?)</script>',plain,__import__('re').S).group(1))
graph['elements'].append({'id':'bad'+chr(10)+'ID','id_source':'explicit','type':'capability','name':'Invalid ID','occurrences':[{'page_id':'capabilities'}]})
graph['elements'].append({'id':'UNDRAWN','id_source':'explicit','type':'capability','name':'Not drawn','occurrences':[]})
for e in graph['elements']:
 if e['id']=='CAP-02': e['id_source']='slug'
plain=__import__('re').sub(r'(id="edgy-graph">).*?(</script>)',lambda m:m[1]+edgy_present._json_for_script(graph)+m[2],plain,flags=__import__('re').S)
Path(sys.argv[1]+'/atlas.html').write_text(h)
Path(sys.argv[1]+'/plain.html').write_text(plain)
punct,_,_,_=test_present._build(test_present.DEMO.replace('CAP-05','CAP/path:05.1'))
Path(sys.argv[1]+'/punct.html').write_text(punct)
` , work], {cwd:root,encoding:'utf8',env:{...process.env,EDGY_TEXT_TABLE_ONLY:'1'}});
if (py.status !== 0) throw new Error(py.stderr || py.stdout);
async function watch(page) {
  await page.exposeFunction('reportCSPViolation', v=>csp.push(v));
  await page.addInitScript(()=>document.addEventListener('securitypolicyviolation', e=>window.reportCSPViolation({directive:e.violatedDirective,blocked:e.blockedURI})));
  page.on('pageerror',e=>errors.push(e.message));
  page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
  page.on('request',r=>{if(/^https?:/.test(r.url()) && !r.url().startsWith(base))network.push(r.url());});
}
async function test(name,fn) { try {await fn();results.push({name,status:'pass'});console.log('PASS',name);}catch(e){results.push({name,status:'fail',error:e.stack});throw e;} }
let browser, server, base;
(async()=>{
 server=http.createServer((req,res)=>{
  const name=req.url.split(/[?#]/)[0];
  const file=name==='/demo.html'?demo:name==='/atlas.html'?path.join(work,'atlas.html'):name==='/plain.html'?path.join(work,'plain.html'):null;
  if(!file){res.writeHead(404);res.end();return;}res.setHeader('Content-Type','text/html; charset=utf-8');res.end(fs.readFileSync(file));
 });
 await new Promise(r=>server.listen(0,'127.0.0.1',r));base='http://127.0.0.1:'+server.address().port;
 browser=await chromium.launch({executablePath:exe,args:['--no-sandbox','--disable-gpu','--disable-software-rasterizer', ...(process.env.EDGY_SINGLE_PROCESS?['--no-zygote','--single-process']:[])]});
 const context=await browser.newContext({viewport:{width:1440,height:1000},reducedMotion:'reduce'});
 const page=await context.newPage();await watch(page);
 for(const origin of ['file','http']) {
  const url=origin==='file'?'file://'+demo:base+'/demo.html';
  await page.goto(url);await page.waitForFunction(()=>document.querySelector('#atlas-frame').contentWindow.EDGY_PRESENT);
  const api=async(method,...args)=>page.locator('#atlas-frame').evaluate((f,[m,a])=>f.contentWindow.EDGY_PRESENT[m](...a),[method,args]);
  await api('getState');
  await test('NV-01/BR-01 all-section return '+origin, async()=>{
   const sections=await page.locator('.nav').count();
   for(let i=0;i<sections;i++){if(i===8)continue;await page.locator(`.nav[data-step="${i}"]`).click();await page.locator('.nav[data-step="8"]').click();await page.locator('#return-story').click();assert.equal(await page.locator('.nav[aria-current="page"]').getAttribute('data-step'),String(i));}
   await page.locator('.nav[data-step="4"]').click();await page.locator('[data-option="2"]').click();await page.locator('.nav[data-step="8"]').click();await page.locator('#return-story').click();assert(await page.locator('[data-option="2"]').evaluate(e=>e.classList.contains('active')));
  });
  await test('NV-02 targeted composition drill '+origin,async()=>{
   await page.locator('.nav[data-step="3"]').click();await page.locator('[data-cap="CAP-02"]').click();await page.locator('[data-open-atlas]').click();await page.waitForFunction(()=>document.querySelector('#atlas-status').textContent.includes('CAP-02'));
   assert.equal((await api('getState')).elementId,'CAP-02');assert.match((await api('getState')).route,/trace/);await page.locator('#return-story').click();assert.equal(await page.evaluate(()=>document.activeElement.dataset.cap),'CAP-02');
  });
  await test('NV-03 rejected targets retain state '+origin,async()=>{
   const before=await api('getState');for(const id of ['MISSING','__proto__',null,{},'<img>'])assert.equal(await api('openElement',id),false);
   for(const route of ['https://example.invalid','#/trace/%ZZ','#/trace/MISSING','#/view/missing','#/view/kyvykkyydet/%ZZ',{}])assert.equal(await api('navigate',route),false);
   assert.deepEqual(await api('getState'),before);
  });
  await test('NV-05/06 srcdoc local back and serial commands '+origin,async()=>{
   await api('navigate','#/');const before=await api('getState');await page.locator('#atlas-frame').evaluate(async f=>{const a=f.contentWindow.EDGY_PRESENT;await Promise.all([a.openElement('JRN-01'),a.openElement('CAP-02')]);});assert.equal((await api('getState')).elementId,'CAP-02');
   assert.equal(await api('back'),true);assert.equal((await api('getState')).elementId,'JRN-01');await api('back');assert.equal((await api('getState')).route,before.route);
  });
  await test('BR-01 discussion/export '+origin,async()=>{
   await page.locator('.nav[data-step="1"]').click();await page.locator('#pause').click();await page.locator('#discussion-note').fill('Test observation');await page.locator('#discussion-owner').fill('Architect');await page.locator('#save-discussion').click();await page.locator('#pause').click();assert.equal(await page.locator('#discussion-note').inputValue(),'Test observation');await page.keyboard.press('Escape');
   await page.locator('.nav[data-step="7"]').click();const [download]=await Promise.all([page.waitForEvent('download'),page.locator('#export-notes').click()]);const file=await download.path();const note=fs.readFileSync(file,'utf8');assert(note.includes('Test observation')&&note.includes('ei muodollinen hyväksyntä'));
  });
 }
 await test('NV-02/03 occurrence fallback / slug / undrawn',async()=>{
  await page.goto('file://'+path.join(work,'plain.html'));await page.waitForFunction(()=>window.EDGY_PRESENT);await page.evaluate(()=>EDGY_PRESENT.ready);
  assert.equal(await page.evaluate(()=>EDGY_PRESENT.openElement('CAP-05')),true);assert.equal((await page.evaluate(()=>EDGY_PRESENT.getState())).elementId,'CAP-05');const before=await page.evaluate(()=>EDGY_PRESENT.getState());
  for(const id of ['CAP-02','UNDRAWN','bad\nID'])assert.equal(await page.evaluate(id=>EDGY_PRESENT.openElement(id),id),false);assert.deepEqual(await page.evaluate(()=>EDGY_PRESENT.getState()),before);
 });
 await test('NV-02/03 API identity and native occurrence Back regressions',async()=>{
  await page.goto('file://'+path.join(work,'atlas.html'));await page.evaluate(()=>EDGY_PRESENT.ready);
  assert.equal(await page.evaluate(()=>EDGY_PRESENT.navigate('#/view/trace-cap-05/AST-02')),true);
  let state=await page.evaluate(()=>EDGY_PRESENT.getState());assert.equal(state.elementId,'AST-02');assert.equal(state.route,'#/view/trace-cap-05/AST-02');
  await page.evaluate(()=>EDGY_PRESENT.navigate('#/view/capabilities'));assert.equal((await page.evaluate(()=>EDGY_PRESENT.getState())).elementId,null);
  await page.evaluate(()=>EDGY_PRESENT.openElement('CAP-05'));assert((await page.locator('#inspector').textContent()).includes('CAP-05'));
  for(const host of ['file://'+path.join(work,'plain.html'),base+'/plain.html']){
   await page.goto(host);await page.evaluate(()=>EDGY_PRESENT.ready);await page.evaluate(()=>EDGY_PRESENT.openElement('CAP-05'));await page.evaluate(()=>EDGY_PRESENT.openElement('AST-02'));await page.goBack();await page.waitForFunction(()=>EDGY_PRESENT.getState().elementId==='CAP-05');
  }
 });
 await test('NV-04 initial route and standalone history',async()=>{
  await page.goto('file://'+path.join(work,'atlas.html')+'#/trace/JRN-01');await page.evaluate(()=>EDGY_PRESENT.ready);assert.equal((await page.evaluate(()=>EDGY_PRESENT.getState())).elementId,'JRN-01');
  await page.evaluate(()=>EDGY_PRESENT.openElement('CAP-05'));await page.goBack();await page.waitForFunction(()=>EDGY_PRESENT.getState().elementId==='JRN-01');await page.goForward();await page.waitForFunction(()=>EDGY_PRESENT.getState().elementId==='CAP-05');
  await page.goto(base+'/demo.html');await page.locator('#atlas-frame').evaluate(f=>{f.srcdoc=f.srcdoc.replace('<html ', '<html data-edgy-start="#/trace/CAP-02" ');});await page.waitForFunction(()=>document.querySelector('#atlas-frame').contentWindow.EDGY_PRESENT?.getState().elementId==='CAP-02');
 });
 await test('NV-04/SE-01 encoded IDs and inert prototype keys',async()=>{
  await page.goto('file://'+path.join(work,'punct.html'));await page.evaluate(()=>EDGY_PRESENT.ready);
  assert.equal(await page.evaluate(()=>EDGY_PRESENT.openElement('CAP/path:05.1')),true);assert.equal((await page.evaluate(()=>EDGY_PRESENT.getState())).elementId,'CAP/path:05.1');
  const route=await page.evaluate(()=>EDGY_PRESENT.getState().route);assert(route.includes('CAP%2Fpath%3A05.1'));
  await page.reload();await page.evaluate(()=>EDGY_PRESENT.ready);assert.equal((await page.evaluate(()=>EDGY_PRESENT.getState())).elementId,'CAP/path:05.1');
  assert.equal(await page.evaluate(()=>EDGY_PRESENT.openElement('constructor')),true);assert.equal((await page.evaluate(()=>EDGY_PRESENT.getState())).elementId,'constructor');
 });
 await test('NV-05 duplicate route native/local history regression',async()=>{
  for(const host of ['file://'+path.join(work,'atlas.html'),base+'/atlas.html']){
   await page.goto(host);await page.evaluate(()=>EDGY_PRESENT.ready);
   for(const route of ['#/view/capabilities','#/view/applications','#/view/capabilities'])await page.evaluate(r=>EDGY_PRESENT.navigate(r),route);
   await page.goBack();await page.waitForFunction(()=>EDGY_PRESENT.getState().pageId==='applications');
   await page.goBack();await page.waitForFunction(()=>EDGY_PRESENT.getState().pageId==='capabilities');
   assert.equal(await page.evaluate(()=>EDGY_PRESENT.back()),true);
   assert.equal((await page.evaluate(()=>EDGY_PRESENT.getState())).route,'#/');
   assert.equal((await page.evaluate(()=>EDGY_PRESENT.getState())).canGoBack,false);
   assert.equal(await page.evaluate(()=>EDGY_PRESENT.back()),false);
  }
 });
 await test('NV-05 native forward, branch and host state history regression',async()=>{
  await page.goto(base+'/atlas.html');await page.evaluate(()=>EDGY_PRESENT.ready);
  await page.evaluate(()=>history.replaceState({hostValue:'preserved'},'',location.href));
  for(const route of ['#/view/capabilities','#/view/applications','#/view/capabilities'])await page.evaluate(r=>EDGY_PRESENT.navigate(r),route);
  await page.goBack();await page.waitForFunction(()=>EDGY_PRESENT.getState().pageId==='applications');
  await page.goForward();await page.waitForFunction(()=>EDGY_PRESENT.getState().pageId==='capabilities');
  await page.evaluate(()=>EDGY_PRESENT.back());assert.equal((await page.evaluate(()=>EDGY_PRESENT.getState())).pageId,'applications');
  await page.evaluate(()=>EDGY_PRESENT.openElement('CAP-05'));
  await page.goBack();await page.waitForFunction(()=>EDGY_PRESENT.getState().pageId==='applications');
  await page.evaluate(()=>EDGY_PRESENT.back());assert.equal((await page.evaluate(()=>EDGY_PRESENT.getState())).pageId,'capabilities');
  assert.equal(await page.evaluate(()=>history.state.hostValue),'preserved');
  await page.goto(base+'/atlas.html#/trace/CAP-05');await page.evaluate(()=>EDGY_PRESENT.ready);await page.reload();await page.evaluate(()=>EDGY_PRESENT.ready);
  await page.evaluate(()=>EDGY_PRESENT.back());assert.equal((await page.evaluate(()=>EDGY_PRESENT.getState())).route,'#/');
 });
 await test('NV-02/05 trace inspector restored on local/native return',async()=>{
  await page.goto('file://'+path.join(work,'atlas.html'));await page.evaluate(()=>EDGY_PRESENT.ready);
  await page.evaluate(()=>EDGY_PRESENT.navigate('#/view/trace-ast-02'));assert.equal((await page.evaluate(()=>EDGY_PRESENT.getState())).route,'#/trace/AST-02');assert((await page.locator('#inspector').textContent()).includes('AST-02'));await page.evaluate(()=>EDGY_PRESENT.back());assert.equal((await page.evaluate(()=>EDGY_PRESENT.getState())).route,'#/');
  await page.evaluate(()=>EDGY_PRESENT.openElement('AST-02'));await page.evaluate(()=>EDGY_PRESENT.openElement('CAP-05'));
  await page.evaluate(()=>EDGY_PRESENT.back());assert.equal((await page.evaluate(()=>EDGY_PRESENT.getState())).elementId,'AST-02');assert((await page.locator('#inspector').textContent()).includes('AST-02'));
  await page.evaluate(()=>EDGY_PRESENT.openElement('CAP-05'));await page.goBack();await page.waitForFunction(()=>EDGY_PRESENT.getState().elementId==='AST-02');assert((await page.locator('#inspector').textContent()).includes('AST-02'));
 });
 await test('BR-03 layout/keyboard/print',async()=>{
  await page.goto('file://'+demo);for(const width of [1440,390]){await page.setViewportSize({width,height:1000});for(let i=0;i<10;i++){await page.evaluate(i=>document.querySelector(`.nav[data-step="${i}"]`).click(),i);assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));}}
  await page.setViewportSize({width:1440,height:1000});await page.locator('.nav[data-step="3"]').click();await page.locator('[data-cap="CAP-02"]').focus();await page.keyboard.press('Enter');assert(await page.locator('#detail-dialog').isVisible());await page.keyboard.press('Escape');assert.equal(await page.evaluate(()=>document.activeElement.dataset.cap),'CAP-02');
  await page.emulateMedia({media:'print'});assert.equal(await page.locator('.chapter:visible').count(),10);await page.pdf({path:path.join(reportDir,'walkthrough.pdf'),preferCSSPageSize:true});await page.emulateMedia({media:'screen'});
  await page.screenshot({path:path.join(reportDir,'walkthrough.png'),fullPage:true});
  await page.setViewportSize({width:390,height:844});await page.reload();await page.keyboard.press('Tab');assert.equal(await page.evaluate(()=>document.activeElement.id),'menu');
  await page.keyboard.press('Enter');assert(await page.locator('#rail').evaluate(e=>e.classList.contains('open')));await page.keyboard.press('Escape');assert.equal(await page.evaluate(()=>document.activeElement.id),'menu');
  await page.setViewportSize({width:1440,height:1000});

 });
 await test('SE-01 hostile narrative data is text',async()=>{
  const text=fs.readFileSync(demo,'utf8');const poisoned=text.replace(/(<script type="application\/json" id="example-data">)(.*?)(<\/script>)/s,(_,a,b,c)=>{const d=JSON.parse(b);const evil='<img src="https://example.invalid/x" onerror="window.pwned=1">';d.sources[0].title=evil;d.sources[0].content=evil;d.capabilities[0].name=evil;d.journey[0].name=evil;d.options[0].title=evil;return a+JSON.stringify(d).replace(/</g,'\\u003c')+c;});
  const file=path.join(work,'hostile.html');fs.writeFileSync(file,poisoned);await page.goto('file://'+file);assert.equal(await page.locator('img[src^="https:"]').count(),0);assert.equal(await page.evaluate(()=>window.pwned),undefined);assert(await page.locator('body').textContent().then(s=>s.includes('<img src=')));
 });
 await test('AC-01 automated AA checks',async()=>{
  await page.goto('file://'+demo);const scans=[];for(const step of [0,2,3,4,7,8,9]){await page.evaluate(i=>document.querySelector(`.nav[data-step="${i}"]`).click(),step);const r=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21a','wcag21aa']).analyze();scans.push({step,violations:r.violations});}
  await page.evaluate(()=>document.querySelector('.nav[data-step="3"]').click());await page.locator('[data-cap="CAP-02"]').click();scans.push({dialog:true,violations:(await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21a','wcag21aa']).analyze()).violations});await page.keyboard.press('Escape');
  const frame=page.frameLocator('#atlas-frame');await page.locator('.nav[data-step="8"]').click();await page.locator('#atlas-frame').evaluate(async f=>{await f.contentWindow.EDGY_PRESENT.ready;await f.contentWindow.EDGY_PRESENT.openElement('CAP-02');});
  scans.push({trace:true,violations:(await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21a','wcag21aa']).analyze()).violations});
  await frame.locator('#btn-search').click();scans.push({search:true,violations:(await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21a','wcag21aa']).analyze()).violations});
  await frame.locator('#palette input').fill('NO-SUCH-XYZ-999');scans.push({emptySearch:true,violations:(await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21a','wcag21aa']).analyze()).violations});
  await frame.locator('#palette input').press('Escape');assert.equal(await frame.locator('#btn-search').evaluate(e=>e===document.activeElement),true);
  fs.writeFileSync(path.join(reportDir,'accessibility.json'),JSON.stringify(scans,null,2));assert.equal(scans.flatMap(s=>s.violations).length,0,JSON.stringify(scans.flatMap(s=>s.violations).map(v=>({id:v.id,impact:v.impact,nodes:v.nodes.map(n=>n.target)}))));
 });
 await test('BR-02 no errors/external requests',async()=>{assert.deepEqual(errors,[]);assert.deepEqual(network,[]);assert.deepEqual(csp,[]);});
})().catch(e=>{console.error(e.stack);process.exitCode=1;}).finally(async()=>{
 fs.writeFileSync(path.join(reportDir,'results.json'),JSON.stringify({results,errors,network,csp,environment:{node:process.version,chromium:browser?browser.version():null},humanAcceptance:'not performed'},null,2));
 console.log('Evidence:',reportDir);if(browser)await browser.close();if(server)await new Promise(r=>server.close(r));
});

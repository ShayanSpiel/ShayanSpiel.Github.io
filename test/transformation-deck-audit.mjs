import puppeteer from 'puppeteer';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
const origin=process.env.DECK_AUDIT_ORIGIN||'http://localhost:4334';
const route=process.env.DECK_AUDIT_PATH||'/ai-transformation/';
const forward=route.startsWith('/fa/')?'ArrowLeft':'ArrowRight';
const backward=route.startsWith('/fa/')?'ArrowRight':'ArrowLeft';
const output=process.env.DECK_AUDIT_DIR||'/tmp/spielos-transformation-deck-audit';
await fs.mkdir(output,{recursive:true});
const browser=await puppeteer.launch({headless:true,executablePath:process.env.CHROME_PATH||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
const page=await browser.newPage();const errors=[];
page.on('pageerror',e=>errors.push(e.message));
await page.setRequestInterception(true);page.on('request',r=>{new URL(r.url()).origin===origin||r.url().startsWith('data:')?r.continue():r.abort();});
await page.emulateMediaFeatures([{name:'prefers-reduced-motion',value:'reduce'}]);
await page.setViewport({width:1680,height:940});
await page.goto(`${origin}${route}`,{waitUntil:'networkidle0'});
await page.waitForSelector('.transformation-deck[data-slide="1"]');
await page.evaluate(()=>document.fonts.ready);
const reports=[];
const total=Number(await page.$eval(".transformation-deck",e=>e.dataset.slideCount));
for(const [width,height] of [[1680,940],[1440,900],[1024,768],[844,390],[390,844]]){
 await page.setViewport({width,height});
 for(let id=1;id<=total;id++){
  await page.evaluate(id=>location.hash=`slide-${id}`,id);
  await page.waitForSelector(`.transformation-deck[data-slide="${id}"]`);
  await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
  const report=await page.evaluate(()=>{
   const root=document.querySelector('.transformation-deck'),frame=document.querySelector('.deck-canonical-frame'),heading=document.querySelector('.deck-heading'),tiles=[...document.querySelectorAll('.deck-tile,.deck-composition')],r=e=>e.getBoundingClientRect(),f=r(frame),h=r(heading);
   const portrait=getComputedStyle(frame).visibility==='hidden';
   const faults=[];
   if(!portrait){
    for(const tile of tiles){const t=r(tile),id=tile.dataset.node;if(t.left<h.right&&t.right>h.left&&t.top<h.bottom&&t.bottom>h.top)faults.push(`${id}: intersects title`);
     if(t.left<f.left-1||t.right>f.right+1||t.top<f.top-1||t.bottom>f.bottom+1)faults.push(`${id}: outside canonical frame`);
     for(const child of tile.querySelectorAll('li,p,code,header,section,footer,.deck-providers,.deck-system-grid,.deck-context-cells,.memory-return,.os-statusbar')){if(getComputedStyle(child).display==='none')continue;const c=r(child);if(c.width===0&&c.height===0)continue;if(c.left<t.left-1||c.right>t.right+1||c.top<t.top-1||c.bottom>t.bottom+1)faults.push(`${id}: content outside tile (${child.tagName})`);}
    }
    for(let i=0;i<tiles.length;i++)for(let j=i+1;j<tiles.length;j++){const a=r(tiles[i]),b=r(tiles[j]);if(Math.min(a.right,b.right)-Math.max(a.left,b.left)>2&&Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top)>2)faults.push(`${tiles[i].dataset.node}: overlaps ${tiles[j].dataset.node}`);}
    for(const edge of document.querySelectorAll('[data-guide-edge-from]')){if(!tiles.some(t=>t.dataset.node===edge.dataset.guideEdgeFrom)||!tiles.some(t=>t.dataset.node===edge.dataset.guideEdgeTo))faults.push('Missing edge endpoint');}
    if(h.top<f.top||h.bottom>f.bottom)faults.push('Title outside frame');
   }
   return {slide:Number(root.dataset.slide),chapter:Number(root.dataset.chapter),portrait,tiles:tiles.length,faults};
  });
  report.viewport=`${width}x${height}`;reports.push(report);
  await page.screenshot({path:`${output}/${width}x${height}-slide-${String(id).padStart(2,'0')}.png`});
 }
 console.log(`Captured all ${total} slides at ${width}×${height}.`);
}
// Real keyboard navigation and history with the film handoff enabled.
await page.setViewport({width:1440,height:900});
await page.emulateMediaFeatures([{name:'prefers-reduced-motion',value:'no-preference'}]);
await page.evaluate(()=>location.hash='slide-6');await page.waitForSelector('[data-slide="6"]');
await page.keyboard.press(forward);await page.waitForSelector('[data-slide="6"][data-leaving="true"]');await page.screenshot({path:`${output}/signature-handoff-outgoing.png`});await page.waitForSelector('[data-slide="7"]');await page.screenshot({path:`${output}/signature-handoff-incoming.png`});
assert.equal(await page.evaluate(()=>location.hash),'#slide-7');
await page.goBack();await page.waitForSelector('[data-slide="6"]');
await page.keyboard.press('Home');await page.waitForSelector('[data-slide="1"]');
await page.keyboard.press(backward);assert.equal(await page.$eval('.transformation-deck',e=>e.dataset.slide),'1');
await page.keyboard.press('End');await page.waitForSelector(`[data-slide="${total}"]`);
await page.keyboard.press(forward);assert.equal(await page.$eval('.transformation-deck',e=>e.dataset.slide),String(total));
const failures=reports.filter(r=>r.faults.length);
await fs.writeFile(`${output}/geometry-report.json`,JSON.stringify({errors,failures,reports},null,2));
await browser.close();
assert.deepEqual(errors,[],'Browser runtime errors');
assert.deepEqual(failures,[],'Composition defects; see geometry-report.json');
console.log(`PASS: ${reports.length} captures, keyboard handoff, history, boundaries, reduced motion. Evidence: ${output}`);

/* One example, authored transitions, measured connections. No analytics or external writes. */
(()=>{
'use strict';
const copy=JSON.parse(document.querySelector('#page-copy').textContent);
const $=(s,r=document)=>r.querySelector(s),$$=(s,r=document)=>[...r.querySelectorAll(s)];
const root=document.documentElement, reduce=matchMedia('(prefers-reduced-motion: reduce)');
const fa=copy.lang==='fa',nf=new Intl.NumberFormat(fa?'fa-IR':'en-US',{maximumFractionDigits:1});
const mobileDiagram=()=>innerWidth<=900||(innerWidth<=950&&innerHeight<=500);
const clamp=x=>Math.min(1,Math.max(0,x)),NS='http://www.w3.org/2000/svg';
let bridges=[],frame=0,approvedWorkflow=false,approvalScroll=0;
const focusEdges=new WeakMap();
root.classList.add('scroll-story');
function svgEl(tag,attrs){const e=document.createElementNS(NS,tag);for(const [k,v]of Object.entries(attrs))e.setAttribute(k,String(v));return e;}
function point(el,within,side='center',fraction=.5){const a=el.getBoundingClientRect(),b=within.getBoundingClientRect();return {x:(side==='left'?a.left:side==='right'?a.right:a.left+a.width*fraction)-b.left,y:(side==='top'?a.top:side==='bottom'?a.bottom:a.top+a.height*.5)-b.top};}
function graphPath(container,from,to,kind='normal',orient='auto'){
 const a=$(from,container),b=$(to,container),svg=$('.graph-lines',container),g=$('g',svg);if(!a||!b)return;
 const focus=container.classList.contains('workflow-diagram')||container.classList.contains('governance-grid');
 let source=a,target=b;
 if(container.classList.contains('workflow-diagram')){
  const ga=a.closest('.agent-workspace'),gb=b.closest('.agent-workspace');
  source=ga&&ga!==gb?ga:($('.wf-node-body',a)||a);
  target=gb&&ga!==gb?gb:($('.wf-node-body',b)||b);
 }
 const ra=source.getBoundingClientRect(),rb=target.getBoundingClientRect();const horizontal=orient==='horizontal'||(orient==='auto'&&Math.abs(ra.left+ra.width/2-rb.left-rb.width/2)>Math.abs(ra.top+ra.height/2-rb.top-rb.height/2));
 let p,q,d;
 if(kind==='return'){
  p=point(source,container,'bottom',mobileDiagram()?.08:.5);q=point($('.ui-icon',b)||target,container,'bottom');
  const lane=mobileDiagram()?2:p.x,under=q.y+25;
  d=`M${p.x} ${p.y} C${p.x} ${p.y+12} ${lane} ${p.y+12} ${lane} ${p.y+24} L${lane} ${under-10} Q${lane} ${under} ${lane+10} ${under} L${q.x-10} ${under} Q${q.x} ${under} ${q.x} ${under-10} L${q.x} ${q.y}`;
 }else if(kind==='department-trunk'){
  p=point(a,container,'bottom');const br=b.getBoundingClientRect(),ar=a.getBoundingClientRect();q=point(b,container,br.left+br.width/2<ar.left+ar.width/2?'right':'left');d=`M${p.x} ${p.y} L${p.x} ${q.y-8} Q${p.x} ${q.y} ${p.x+(q.x-p.x)*.5} ${q.y} L${q.x} ${q.y}`;
 }else if(kind==='side'){
  p=point(source,container,'right');q=point(target,container,'right');const edge=container.clientWidth-2;
  d=`M${p.x} ${p.y} C${edge} ${p.y} ${edge} ${p.y+35} ${edge} ${p.y+65} L${edge} ${q.y-35} Q${edge} ${q.y} ${q.x} ${q.y}`;
 }else if(horizontal){
  const dir=rb.left>ra.left,aa=a.classList.contains('pathway-step')?($('.logo-plaque',a)||$('.ui-icon',a)):source,bb=b.classList.contains('pathway-step')?($('.logo-plaque',b)||$('.ui-icon',b)):target;p=point(aa,container,dir?'right':'left');q=point(bb,container,dir?'left':'right');const mid=(p.x+q.x)/2;
  d=`M${p.x} ${p.y} C${mid} ${p.y} ${mid} ${q.y} ${q.x} ${q.y}`;
 }else{
  const down=rb.top>ra.top,aa=a.classList.contains('pathway-step')?($('.logo-plaque',a)||$('.ui-icon',a)):source,bb=b.classList.contains('pathway-step')?($('.logo-plaque',b)||$('.ui-icon',b)):target;const lane=focus&&container.classList.contains('workflow-diagram')&&mobileDiagram()?(fa?.16:.84):.5;p=point(aa,container,down?'bottom':'top',lane);q=point(bb,container,down?'top':'bottom',lane);const mid=(p.y+q.y)/2;
  d=`M${p.x} ${p.y} C${p.x} ${mid} ${q.x} ${mid} ${q.x} ${q.y}`;
 }
 const pth=svgEl('path',{d,'data-edge':from+'>'+to,class:kind==='blocked'?'graph-future':kind==='return'?'graph-return':''});
 if(focus){
  const group=svgEl('g',{class:'flow-edge','data-edge':from+'>'+to,'data-kind':kind});
  const track=svgEl('path',{d,class:'flow-track'}),head=svgEl('polyline',{class:'flow-head'});
  pth.classList.add('flow-active');group.append(track,pth,head);
  group.dataset.targetX=q.x;group.dataset.targetY=q.y;group.append(svgEl('circle',{cx:p.x,cy:p.y,r:2.5,class:'flow-port','data-port':'source'}));
  g.append(group);focusEdges.set(pth,{head,group});drawEdge(pth,kind==='return'||kind==='blocked'?0:1);
 }else{
  g.append(pth);
  if(!['return','blocked','side'].includes(kind)){const length=pth.getTotalLength(),base=pth.getPointAtLength(Math.max(0,length-1)),dx=q.x-base.x,dy=q.y-base.y,n=Math.hypot(dx,dy)||1,ux=dx/n,uy=dy/n;g.append(svgEl('polyline',{points:`${q.x-ux*7-uy*3.5},${q.y-uy*7+ux*3.5} ${q.x},${q.y} ${q.x-ux*7+uy*3.5},${q.y-uy*7-ux*3.5}`,class:'graph-arrow'}));}
  g.append(svgEl('circle',{cx:p.x,cy:p.y,r:2.1}));
 }

}
function measureGraphs(){
 $$('[data-graph]').forEach(el=>{const s=$('.graph-lines',el);s.setAttribute('viewBox',`0 0 ${el.clientWidth} ${el.clientHeight}`);$('g',s).replaceChildren();});
 const hero=$('.order-half');for(let i=0;i<3;i++)graphPath(hero,`#hero-team-${i}`,'#hero-os','normal','vertical');for(const id of ['work','control','metric'])graphPath(hero,'#hero-os',`#hero-${id}`,'normal','vertical');
 const pathway=$('.pathway');for(let i=0;i<4;i++)graphPath(pathway,`#pathway-${i}`,`#pathway-${i+1}`,'normal',mobileDiagram()?'vertical':'horizontal');
 const w=$('.workflow-diagram');for(let i=0;i<4;i++)graphPath(w,`#wf-${i}`,`#wf-${i+1}`,'normal',mobileDiagram()||i===1?'vertical':'horizontal');
 graphPath(w,'#wf-2','#wf-blocked',mobileDiagram()?'side':'blocked','vertical');
 graphPath(w,'#wf-4','#wf-feedback','return','vertical');
 const gov=$('.governance-grid');graphPath(gov,'#permissions','#approval-gate','normal',mobileDiagram()?'vertical':'horizontal');graphPath(gov,'#approval-gate','#audit-log','normal','vertical');
 const sys=$('.system-assembly');for(let i=0;i<6;i++)graphPath(sys,mobileDiagram()?'#assembly-core .os-control-layer':'#assembly-core .os-object',`#system-${i}`,mobileDiagram()?'department-trunk':'normal','auto');graphPath(sys,'#system-lead','#assembly-core .os-object','normal','vertical');
}
function measureBridges(){
 bridges=[];
 $$('.story-bridge').forEach((el,i)=>{
  const from=$(el.dataset.from),to=$(el.dataset.to),svg=$('svg',el);if(!from||!to)return;
  const box=el.getBoundingClientRect(),a=from.getBoundingClientRect(),b=to.getBoundingClientRect(),width=innerWidth;
  const side=b.width<600?(b.left+b.width/2>width/2?width-14:14):(i%2===0?(fa?width-14:14):(fa?14:width-14));
  const af=a.width<240?.5:side>width/2?.78:.22,bf=b.width<240?.5:side>width/2?.82:.18;
  const start=a.bottom+2,end=b.top-2,h=Math.max(40,end-start),x1=a.left+a.width*af,x2=b.left+b.width*bf;
  const turn=Math.min(80,h*.17),landing=Math.min(65,h*.14);
  const d=`M${x1} 0 C${x1} ${turn*.6} ${side} ${turn*.3} ${side} ${turn} C${side} ${h*.38} ${side} ${h*.64} ${side} ${h-landing} C${side} ${h-landing*.4} ${x2} ${h-landing} ${x2} ${h}`;
  svg.style.top=`${start-box.top}px`;svg.style.width=`${width}px`;svg.style.height=`${h}px`;svg.setAttribute('viewBox',`0 0 ${width} ${h}`);
  const core=$('.bridge-core',el),future=$('.bridge-future',el);core.setAttribute('d',d);future.setAttribute('d',d);
  const len=core.getTotalLength(),scale=Math.max(.55,Math.min(1,width/1680));core.style.strokeWidth=String(6*scale);
  bridges.push({el,svg,core,len,start:start+scrollY,h,tip:$('.bridge-tip',el),head:$('.bridge-arrow',el),scale,to,arrived:false});
 });paintScroll();
}
/* A single scroll clock drives both the signature and the scenes. No elapsed-time playback. */
function sceneProgress(el,start=.82,finish=.30){
 const r=el.getBoundingClientRect();
 return reduce.matches?1:clamp((innerHeight*start-r.top)/Math.max(innerHeight*.56,r.height+innerHeight*(start-finish)-innerHeight));
}
function drawEdge(edge,p){
 if(!edge)return;const len=edge.getTotalLength(),progress=clamp(p),record=focusEdges.get(edge);
 edge.style.strokeDasharray=`${len*progress} ${len}`;edge.style.strokeDashoffset='0';
 if(record){
  const at=progress>.015?len*progress:len,tip=edge.getPointAtLength(at),behind=edge.getPointAtLength(Math.max(0,at-2));
  const dx=tip.x-behind.x,dy=tip.y-behind.y,n=Math.hypot(dx,dy)||1,ux=dx/n,uy=dy/n,l=9,w=4.6;
  record.head.setAttribute('points',`${tip.x-ux*l-uy*w},${tip.y-uy*l+ux*w} ${tip.x},${tip.y} ${tip.x-ux*l+uy*w},${tip.y-uy*l-ux*w}`);
  record.group.classList.toggle('flow-drawn',progress>.015);record.group.dataset.progress=progress.toFixed(3);
  record.head.style.opacity=progress>.015&&at<l?0:1;
 }
}
function paintScenes(){
 const scene=$('.reality-scene'),hp=sceneProgress(scene,.94,.25);
 scene.dataset.scrollProgress=hp.toFixed(3);
 $$('.chaos-task').forEach((el,i)=>{const p=reduce.matches?1:clamp(hp*2.2-i*.16);el.style.opacity=String(.3+.7*p);el.style.translate=`0 ${(1-p)*15}px`;});
 const ordered=$('.order-half'),op=sceneProgress(ordered,.88,.34);
 ordered.style.setProperty('--scene-progress',op.toFixed(3));
 $$('.order-half .graph-lines path').forEach((el,i)=>drawEdge(el,op*1.6-i*.1));
 $$('.hero-teams,.hero-os,.hero-outcomes').forEach((el,i)=>el.style.opacity=String(.30+.70*clamp(op*1.7-i*.17)));
 const dashboard=$('#dashboard'),dp=sceneProgress(dashboard,.9,.28);dashboard.dataset.scrollProgress=dp.toFixed(3);
 $$('[data-count]',dashboard).forEach(el=>{const p=clamp(dp*1.7),end=+el.dataset.count;el.textContent=nf.format(Math.round(end*p))+(el.dataset.suffix||'');});
 const cp=sceneProgress($('.monitor-results'),.88,.40);drawEdge($('.animated-chart'),cp);
 paintWorkflow();
 const gov=$('.governance-grid');
 $$('.permission-row',gov).forEach(el=>el.style.opacity='1');
 $$('.graph-lines path[data-edge]',gov).forEach((el,i)=>drawEdge(el,sceneProgress(i===0?$('#approval-gate'):$('#audit-log'),.88,.38)));
 const sys=$('.system-assembly'),sp=sceneProgress(sys,.86,.32);sys.dataset.scrollProgress=sp.toFixed(3);
 $$('.department-node',sys).forEach((el,i)=>{
  const p=mobileDiagram()?sceneProgress(el,.9,.48):clamp(sp*1.65-(i%3)*.17);
  el.style.setProperty('--node-progress',p.toFixed(3));el.style.opacity=String(.30+.70*p);
  drawEdge($(`path[data-edge$=">#system-${i}"]`,sys),p);
 });
 drawEdge($('path[data-edge^="#system-lead"]',sys),sceneProgress($('#system-lead'),.88,.46));
 $$('[data-reveal]').forEach(el=>{el.classList.add('is-visible');el.style.setProperty('--scroll-reveal',sceneProgress(el,.96,.48).toFixed(3));});
}
function paintWorkflow(){
 const diagram=$('.workflow-diagram'),r=diagram.getBoundingClientRect(),span=Math.max(innerHeight*.65,r.height-innerHeight*.18);
 let raw=reduce.matches?4:clamp((innerHeight*.82-r.top)/span)*4;
 if(mobileDiagram()&&!reduce.matches){
  const centers=$$('[data-step]').map(el=>{const b=el.getBoundingClientRect();return b.top+b.height*.5;}),readingLine=innerHeight*.55;raw=0;
  for(let i=0;i<4;i++)if(readingLine>=centers[i])raw=i+clamp((readingLine-centers[i])/Math.max(1,centers[i+1]-centers[i]));
 }
 let position=Math.min(3,raw);
 if(approvedWorkflow){const last=$('#wf-4').getBoundingClientRect(),owner=$('#wf-3').getBoundingClientRect(),distance=Math.max(innerHeight*.23,Math.abs(last.top-owner.top));position=Math.min(raw,3+clamp((scrollY-approvalScroll)/distance));}
 const nodes=$$('[data-step]'),approve=$('[data-approve-workflow]'),packet=$('.request-packet'),stage=Math.min(4,Math.floor(position+.001)),fraction=position-stage;
 diagram.dataset.scrollProgress=(position/4).toFixed(3);diagram.dataset.approved=String(approvedWorkflow);
 nodes.forEach((el,i)=>{el.classList.toggle('step-active',i===stage&&position<4);el.classList.toggle('step-complete',i<stage||position>=4);});
 $$('.workflow-diagram .graph-lines path').forEach(el=>{const m=el.dataset.edge?.match(/^#wf-(\d)>#wf-(\d)$/);if(m){const p=clamp(position-Number(m[1]));drawEdge(el,p);el.classList.toggle('active-path',p>0);}});
 const edge=$(`.workflow-diagram path[data-edge="#wf-${stage}>#wf-${stage+1}"]`);
 if(edge&&fraction>.015&&fraction<.985&&!reduce.matches){const point=edge.getPointAtLength(edge.getTotalLength()*fraction);packet.style.opacity='1';packet.style.transform=`translate(${point.x-23}px,${point.y-16}px)`;}else packet.style.opacity='0';
 approve.disabled=position<3||approvedWorkflow;
 const status=position>=4?copy.completed:position>=3?(approvedWorkflow?copy.humanDone:copy.humanWait):copy.scrollWorkflow;
 $('.run-status').textContent=status;
 $('#wf-blocked').classList.toggle('branch-visible',position>=2&&position<3);
 drawEdge($('.workflow-diagram path[data-edge="#wf-2>#wf-blocked"]'),position>=2?1:0);
 drawEdge($('.workflow-diagram path[data-edge="#wf-4>#wf-feedback"]'),position>=4?1:0);
 $('[data-run-workflow] span').textContent=copy.workflowReset;
}
function paintScroll(){
 frame=0;
 for(const b of bridges){
  const y=clamp((scrollY+innerHeight*.58-b.start)/b.h)*b.h;
  let lo=0,hi=b.len;for(let i=0;i<15;i++){const mid=(lo+hi)/2;if(b.core.getPointAtLength(mid).y<y)lo=mid;else hi=mid;}
  const tipLength=reduce.matches?b.len:(lo+hi)/2,progress=tipLength/b.len,baseLength=Math.max(0,tipLength-18.72*1.9*b.scale);
  const tip=b.core.getPointAtLength(tipLength),base=b.core.getPointAtLength(baseLength),ahead=b.core.getPointAtLength(Math.min(b.len,baseLength+1));
  const dx=ahead.x-base.x,dy=ahead.y-base.y,norm=Math.hypot(dx,dy)||1,nx=-dy/norm*15.12*.95*b.scale,ny=dx/norm*15.12*.95*b.scale;
  b.el.dataset.scrollProgress=progress.toFixed(3);
  b.core.style.strokeDasharray=`${baseLength} ${b.len}`;b.core.style.strokeDashoffset='0';
  b.head.setAttribute('points',`${tip.x},${tip.y} ${base.x+nx},${base.y+ny} ${base.x-nx},${base.y-ny}`);b.head.style.opacity=progress>.01?'1':'0';
  const end=b.core.getPointAtLength(b.len);b.tip.setAttribute('transform',`translate(${end.x} ${end.y}) scale(${b.scale*.65})`);b.tip.style.opacity=progress>.96?'.18':'0';
  b.to.classList.toggle('scene-arrived',progress>.98);
 }
 paintScenes();
}
function scheduleScroll(){if(!frame)frame=requestAnimationFrame(paintScroll);}
let measureFrame=0;
function measureAll(){if(measureFrame)cancelAnimationFrame(measureFrame);measureFrame=requestAnimationFrame(()=>{measureGraphs();measureBridges();measureFrame=0;});}
addEventListener('scroll',scheduleScroll,{passive:true});addEventListener('resize',measureAll,{passive:true});
new ResizeObserver(measureAll).observe($('main'));
$('[data-approve-workflow]').addEventListener('click',()=>{approvedWorkflow=true;approvalScroll=scrollY;paintScroll();});
$('[data-run-workflow]').addEventListener('click',()=>{approvedWorkflow=false;approvalScroll=0;$('#workflow').scrollIntoView({behavior:reduce.matches?'instant':'smooth',block:'start'});paintScroll();});
function setUsecase(index){
 const path=copy.paths[index];$$('[data-usecase]').forEach(b=>b.setAttribute('aria-pressed',String(+b.dataset.usecase===index)));
 $$('[data-tool]').forEach(e=>e.classList.toggle('tool-active',path.active.includes(e.dataset.tool)));
 $$('.pathway-step').forEach((el,i)=>{
  const slug=path.slugs[i],label=$('small',el);el.querySelector('.tool-logo')?.remove();el.querySelector('.ui-icon')?.remove();
  if(slug){const span=document.createElement('span');span.className='tool-logo tool-logo--'+slug;const plaque=document.createElement('span');plaque.className='logo-plaque';const img=document.createElement('img');img.src='/assets/logos/'+slug+'.svg';img.alt='';img.width=28;img.height=28;plaque.append(img);const name=document.createElement('bdi');name.textContent=copy.toolNames[slug];span.append(plaque,name);el.prepend(span);}else{const human=$('#wf-3 .ui-icon').cloneNode(true);el.prepend(human);}
  label.textContent=path.labels[i];
 });
 $('[data-path-caption]').textContent=copy.departmentTitles[index];
 $('[data-path-owner]').textContent=copy.departmentOwners[index];
 $('[data-business-input]').textContent=copy.departmentInputs[index];
 $('[data-business-output]').textContent=copy.departmentOutputs[index];
 const panel=$('#selected-path');panel.classList.remove('pathway-changing');void panel.offsetWidth;panel.classList.add('pathway-changing');
 measureAll();
}
let activeDepartment=0,manualDepartment=false,toolHover=false,toolsVisible=false;
const toolMap=$('.department-tool-map'),cycleButton=$('[data-cycle-toggle]'),cycleStatus=$('.cycle-status');
function cycleState(){
 const running=!manualDepartment&&!toolHover&&!reduce.matches;
 toolMap.classList.toggle('cycling',running);cycleButton.textContent=running?(fa?'توقف':'Pause'):(fa?'پخش خودکار':'Auto-play');
 cycleStatus.textContent=manualDepartment?(fa?'انتخاب شما':'Your selection'):(fa?'نمونه‌ها خودکار عوض می‌شن':'Examples cycle automatically');
}
function chooseDepartment(index,manual=false){activeDepartment=index;if(manual)manualDepartment=true;toolMap.classList.remove('cycling');setUsecase(index);void toolMap.offsetWidth;cycleState();}
$$('[data-usecase]').forEach(b=>b.addEventListener('click',()=>chooseDepartment(+b.dataset.usecase,true)));
cycleButton.addEventListener('click',()=>{manualDepartment=!manualDepartment;if(!manualDepartment)toolHover=false;cycleState();});
toolMap.addEventListener('pointerenter',()=>{toolHover=true;cycleState();});toolMap.addEventListener('pointerleave',()=>{toolHover=false;cycleState();});
toolMap.addEventListener('focusin',()=>{toolHover=true;cycleState();});toolMap.addEventListener('focusout',e=>{if(!toolMap.contains(e.relatedTarget)){toolHover=false;cycleState();}});
new IntersectionObserver(entries=>{toolsVisible=entries[0].isIntersecting;},{threshold:.25}).observe(toolMap);
setInterval(()=>{if(toolsVisible&&!manualDepartment&&!toolHover&&!reduce.matches&&!document.hidden)chooseDepartment((activeDepartment+1)%copy.paths.length);},7000);
chooseDepartment(0);reduce.addEventListener('change',cycleState);
$$('[data-approval]').forEach(b=>b.addEventListener('click',()=>{
 const yes=b.dataset.approval==='yes',gov=$('.governance-grid');gov.classList.toggle('approved',yes);
 $$('[data-approval]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));
 $('.gate-result p').textContent=yes?copy.gateSent:copy.gatePreview;$('.gate-result .status-dot').classList.toggle('warning',!yes);
 $('[data-audit-line="2"]').textContent=yes?copy.auditApproved:copy.auditRows[2];
 $$('.governance-grid .graph-lines path[data-edge]').forEach(p=>p.classList.toggle('active-path',yes));
}));
const themeButton=$('.theme-switch');
function themeState(){const paper=root.dataset.theme==='paper-light';if(copy.themeIcons){$('.theme-switch .ui-icon path').setAttribute('d',copy.themeIcons[paper?'moon':'sun']);}themeButton.setAttribute('aria-pressed',String(paper));$('span',themeButton).textContent=paper?copy.dark:copy.light;themeButton.title=fa?(paper?'تم آبی تیره':'تم کاغذی روشن'):(paper?'Dark blue theme':'Light paper theme');$('meta[name="theme-color"]').content=paper?'#eee4d4':'#0b0f1a';}
themeButton.addEventListener('click',()=>{root.dataset.theme=root.dataset.theme==='paper-light'?'blue-dark':'paper-light';try{localStorage.setItem('spielos-home-theme',root.dataset.theme);}catch(e){}themeState();});themeState();
reduce.addEventListener('change',measureAll);
document.fonts.ready.then(measureAll);addEventListener('load',measureAll);measureAll();
})();

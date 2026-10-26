/* Canonical icon ↔ original happy character. No account, AI or runtime access. */
(()=>{'use strict';
 const raw=document.querySelector('#brand-art');if(!raw)return;
 const art=JSON.parse(raw.textContent),NS='http://www.w3.org/2000/svg',reduce=matchMedia('(prefers-reduced-motion: reduce)');
 const hosts=[...document.querySelectorAll('.site-nav .wordmark,.unified-footer .wordmark,.reader-footer .wordmark,.momentum-footer>a:first-child')];
 const el=(tag,attrs)=>{const n=document.createElementNS(NS,tag);for(const[k,v]of Object.entries(attrs))n.setAttribute(k,v);return n;};
 let disposed=false;const instances=[];
 for(const host of hosts){
  host.classList.add('brand-creature');host.querySelector('strong')?.remove();
  const svg=el('svg',{viewBox:'0 0 144 144','aria-hidden':'true'}),g=el('g',{});svg.append(g);host.replaceChildren(svg);
  const marks=[art.mark.line,art.mark.dot,art.mark.xLeft,art.mark.xRight].map((d,i)=>({d,transform:'translate(12 12) scale(5)',paint:'primary',stroke:.65,hidden:false}));
  const original=art.faces.happy;const faces=Array.from({length:4},(_,i)=>({...original[Math.min(i,original.length-1)],hidden:i>=original.length,transform:'translate(9.6 17.6) scale(.88) '+original[Math.min(i,original.length-1)].transform}));
  const paths=marks.map(()=>{const p=el('path',{'stroke-linejoin':'miter','stroke-miterlimit':3,'paint-order':'stroke fill'});g.append(p);return p;});
  function samples(p){const path=el('path',{d:p.d}),m=new DOMMatrix();let mat=m;const tmp=el('g',{transform:p.transform||''});tmp.append(path);svg.append(tmp);mat=tmp.transform.baseVal.consolidate()?.matrix||m;const length=path.getTotalLength();const points=Array.from({length:80},(_,i)=>{const q=path.getPointAtLength(length*i/80);return new DOMPoint(q.x,q.y).matrixTransform(mat);});tmp.remove();return points;}
  const starts=marks.map(samples),ends=faces.map(samples);let mood=false,timer,raf;
  function exact(set){set.forEach((p,i)=>{const q=paths[i];q.setAttribute('d',p.d);q.setAttribute('transform',p.transform||'');q.style.fill=`var(--${p.paint})`;q.style.stroke=`var(--${p.paint})`;q.setAttribute('stroke-width',p.stroke);q.style.opacity=p.hidden?'0':'1';});}
  function turn(target){cancelAnimationFrame(raf);const from=target?starts:ends,to=target?ends:starts,time=performance.now();host.dataset.face=String(target);if(reduce.matches){exact(marks);return;}
   svg.animate([{transform:'rotateY(0deg)'},{transform:'rotateY(88deg)',offset:.42},{transform:'rotateY(0deg)'}],{duration:1100,easing:'cubic-bezier(.25,.65,.25,1)'});
   function frame(now){let v=Math.min(1,(now-time)/950),p=v*v*(3-2*v);paths.forEach((path,i)=>{path.removeAttribute('transform');path.setAttribute('d',from[i].map((a,j)=>`${j?'L':'M'}${(a.x+(to[i][j].x-a.x)*p).toFixed(2)},${(a.y+(to[i][j].y-a.y)*p).toFixed(2)}`).join(' ')+'Z');path.style.fill=`var(--${(target?faces:marks)[i].paint})`;path.style.stroke=path.style.fill;path.setAttribute('stroke-width','1');const opFrom=(target?marks:faces)[i].hidden?0:1,opTo=(target?faces:marks)[i].hidden?0:1;path.style.opacity=String(opFrom+(opTo-opFrom)*p);});if(v<1)raf=requestAnimationFrame(frame);else exact(target?faces:marks);};raf=requestAnimationFrame(frame);
  }
  function schedule(){clearTimeout(timer);if(reduce.matches||disposed)return;timer=setTimeout(()=>{if(!document.hidden){mood=!mood;turn(mood);}schedule();},mood?4200:7200);}
  exact(marks);schedule();host.addEventListener('pointerenter',()=>{if(!reduce.matches&&!mood){mood=true;turn(true);schedule();}});instances.push(()=>{clearTimeout(timer);cancelAnimationFrame(raf);svg.getAnimations().forEach(a=>a.cancel());mood=false;exact(marks);schedule();});
 }
 reduce.addEventListener('change',()=>instances.forEach(f=>f()));addEventListener('pagehide',()=>{disposed=true;instances.forEach(f=>f());},{once:true});
})();

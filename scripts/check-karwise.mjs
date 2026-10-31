import {createHash} from 'node:crypto';
import {readFileSync,existsSync,readdirSync,statSync} from 'node:fs';
import {join,posix} from 'node:path';
const root=process.env.KARWISE_CHECK_ROOT||'dist',origin='https://spielos.xyz',errors=[],pages=new Map(),fail=x=>errors.push(x);
const walk=dir=>readdirSync(dir).flatMap(n=>{let p=join(dir,n);return statSync(p).isDirectory()?walk(p):[p]});
const decode=s=>s.replace(/&amp;/g,'&').replace(/&quot;/g,'"').replace(/&#39;|&apos;/g,"'").replace(/&lt;/g,'<').replace(/&gt;/g,'>');
const attrs=tag=>Object.fromEntries([...tag.matchAll(/([\w:-]+)\s*=\s*(["'])(.*?)\2/gs)].map(m=>[m[1].toLowerCase(),decode(m[3])]));
const tags=(html,name)=>[...(name==='script'?html:html.replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi,'')).matchAll(new RegExp('<'+name+'\\b[^>]*>','gi'))].map(m=>attrs(m[0]));
const local=url=>{try{let u=new URL(url,origin);return u.origin===origin?decodeURIComponent(u.pathname):null}catch{return null}};
const exists=(url,base=origin)=>{let p=local(new URL(url,base).href);return p===null||existsSync(join(root,p))||existsSync(join(root,p,'index.html'))};
const required=['description','robots','og:title','og:description','og:image','og:image:alt','og:type','og:locale','twitter:card','twitter:image','twitter:image:alt','google-site-verification'];
for(const file of walk(root).filter(p=>p.endsWith('.html'))){
 const html=readFileSync(file,'utf8'),route='/'+file.slice(root.length+1).replace(/index\.html$/,''),links=tags(html,'link'),meta=Object.fromEntries(tags(html,'meta').map(a=>[a.name||a.property,a.content])),canonical=links.find(a=>a.rel==='canonical')?.href,redirect=tags(html,'meta').find(a=>a['http-equiv']?.toLowerCase()==='refresh'),indexable=canonical===origin+route&&!redirect&&!meta.robots?.includes('noindex'),doc=attrs(html.match(/<html\b[^>]*>/i)?.[0]||''),alternates=links.filter(a=>a.rel==='alternate'&&a.hreflang),anchors=tags(html,'a');
 const row={route,html,meta,canonical,redirect,indexable,alternates,anchors};pages.set(route,row);
 if(!redirect&&!html.includes('data-kw-navigation'))fail('Missing unified navigation: '+route);
 for(const a of [...links,...tags(html,'script'),...tags(html,'img'),...anchors]){const u=a.href||a.src;if(u&&!exists(u,origin+route))fail('Broken local reference: '+route+' -> '+u)}
 for(const m of html.matchAll(/<script\b[^>]*type=["']application\/ld\+json["'][^>]*>(.*?)<\/script>/gs)){try{JSON.parse(m[1])}catch{fail('Invalid JSON-LD: '+route)}}
 if(redirect){if(!html.includes('location.replace(')||!html.includes('location.search+location.hash')||!html.includes('data-kw-first-paint'))fail('Unsafe/unstyled redirect: '+route);continue;}
 if(!indexable)continue;
 if(doc.dir!==(doc.lang==='fa'?'rtl':'ltr'))fail('Language direction: '+route);
 if(!html.match(/<title>[^<]+<\/title>/))fail('Missing title: '+route);
 if([...html.replace(/<noscript\b[^>]*>[\s\S]*?<\/noscript>/gi,'').matchAll(/<h1\b/gi)].length!==1)fail('H1 count: '+route);
 for(const key of required)if(!meta[key])fail('Missing '+key+': '+route);
 for(const key of ['og:image','twitter:image']){let path=local(meta[key]);if(!path||!exists(meta[key]))fail('Invalid social image: '+route);else{let data=readFileSync(join(root,path));if(data.length<24||data.readUInt32BE(16)!==1200||data.readUInt32BE(20)!==630)fail('Social dimensions: '+route);}}
 if(/(?:https?:\/\/(?:localhost|127\.0\.0\.1)|\/Users\/)/.test(html))fail('Private/staging reference: '+route);
 if(route.endsWith('/contact/')&&(!html.includes('action="https://formsubmit.co/66shayan@gmail.com"')||!html.includes('site-services.js')))fail('Contact form disconnected: '+route);
}
const indexed=[...pages.values()].filter(p=>p.indexable);
const coverManifestPath=join(root,'assets/og/karwise-cover-manifest.json');let coverManifest;
try{coverManifest=JSON.parse(readFileSync(coverManifestPath,'utf8'))}catch{fail('Missing or invalid current OG manifest: run npm run og:generate');coverManifest={pages:[]};}
if(coverManifest.version!=='karwise-og-v5')fail('Unsupported current OG manifest version');
const covers=new Map((coverManifest.pages||[]).map(entry=>[entry.canonical,entry])),coverImages=new Set();
if(covers.size!==indexed.length)fail('Current OG manifest must contain exactly one entry for every canonical page');
for(const p of indexed){const cover=covers.get(p.canonical);if(!cover){fail('Missing current OG manifest entry: '+p.route+' — run npm run og:generate');continue;}
 if(cover.route!==p.route||cover.og_title!==p.meta['og:title']||cover.description!==p.meta['og:description'])fail('OG artwork copy is out of sync with page metadata: '+p.route);
 if(!cover.image?.startsWith('assets/og/v5/')||!cover.sha256)fail('Invalid versioned OG manifest asset: '+p.route);
 if(coverImages.has(cover.image))fail('Canonical pages must have distinct OG images: '+p.route);coverImages.add(cover.image);
 let imageUrl;try{imageUrl=new URL(p.meta['og:image'])}catch{fail('Invalid OG image URL: '+p.route);continue;}
 if(imageUrl.pathname!=='/'+cover.image||imageUrl.searchParams.get('v')!==cover.sha256.slice(0,12)||p.meta['twitter:image']!==p.meta['og:image'])fail('OG and Twitter image do not match the generated cover: '+p.route);
 const imageFile=join(root,cover.image);if(!existsSync(imageFile)){fail('Missing generated OG image: '+p.route);continue;}
 if(createHash('sha256').update(readFileSync(imageFile)).digest('hex')!==cover.sha256)fail('OG manifest hash mismatch: '+p.route);
}
for(const canonical of covers.keys())if(!indexed.some(p=>p.canonical===canonical))fail('Stale OG manifest route: '+canonical);
for(const field of ['title','description']){let seen=new Map();for(const p of indexed){let value=field==='title'?p.html.match(/<title>(.*?)<\/title>/s)?.[1]:p.meta.description;if(seen.has(value))fail('Duplicate '+field+': '+p.route+' / '+seen.get(value));seen.set(value,p.route);}}
for(const p of indexed){const cluster=JSON.stringify(p.alternates.map(a=>[a.hreflang,a.href]).sort());for(const a of p.alternates){const other=pages.get(local(a.href));if(!other?.indexable)fail('Noncanonical language target: '+p.route+' -> '+a.href);else if(cluster!==JSON.stringify(other.alternates.map(a=>[a.hreflang,a.href]).sort()))fail('Asymmetric languages: '+p.route);}
 for(const a of p.anchors){if(pages.get(local(a.href))?.redirect)fail('Internal link to redirect: '+p.route+' -> '+a.href);}}
const sitemap=new Set([...readFileSync(join(root,'sitemap.xml'),'utf8').matchAll(/<loc>(.*?)<\/loc>/g)].map(m=>decode(m[1]))),canonical=new Set(indexed.map(p=>p.canonical));
for(const url of [...sitemap,...canonical])if(sitemap.has(url)!==canonical.has(url))fail('Sitemap mismatch: '+url);
const reachable=new Set(),queue=['/','/en/'];while(queue.length){let r=queue.pop();if(reachable.has(r))continue;reachable.add(r);for(const a of pages.get(r)?.anchors||[]){let p=local(a.href);if(pages.has(p)&&!reachable.has(p))queue.push(p);}}
for(const p of indexed)if(!reachable.has(p.route))fail('Orphan canonical page: '+p.route);
const tokens=readFileSync(join(root,'design-tokens.css'),'utf8');for(const key of ['--radius-sm','--radius-md','--journey-core','--journey-future','--finish-light-ffffff15','--stage-observe','--brand-surface-fill','--brand-depth'])if(!tokens.includes(key+':'))fail('Required design token missing: '+key);
// CSS intrinsic font descriptors, SVG payloads and responsive/vector geometry remain authored data.
for(const file of walk(root).filter(p=>p.endsWith('.css')&&!p.endsWith('/design-tokens.css'))){let css=readFileSync(file,'utf8').replace(/\/\*[\s\S]*?\*\//g,'').replace(/@font-face\s*\{[^}]*\}/g,'').replace(/url\([^)]*\)/g,'url()');for(const m of css.matchAll(/(?:^|[;{])\s*([\w-]+)\s*:\s*([^;{}]+)/g)){if(/#[a-f0-9]{3,8}\b/i.test(m[2])&&!m[1].startsWith('--'))fail('Hardcoded CSS color: '+file+' '+m[1]);if(['border-radius','font-size'].includes(m[1])&&/\d/.test(m[2])&&!m[2].includes('var(')&&m[2].replace(/!important/g,'').trim()!=='0')fail('Hardcoded design size: '+file+' '+m[1]);}}
if(!readFileSync(join(root,'index.html'),'utf8').includes('lang="fa"'))fail('Default homepage is not Persian');
if(!readFileSync(join(root,'404.html'),'utf8').includes('noindex'))fail('404 must be noindex');
for(const lang of ['fa','en']){const html=pages.get('/'+lang+'/guides/')?.html||'';for(const tone of ['learn','design','evaluate','success'])if((html.match(new RegExp('data-journey-tone="'+tone+'"','g'))||[]).length!==1)fail('Missing or duplicate journey badge: '+lang+' '+tone);if(html.includes('class="kw-journey-goal"'))fail('Duplicate journey success target: '+lang);}
if(errors.length){console.error([...new Set(errors)].join('\n'));throw Error(`${errors.length} full-site checks failed`)}
console.log(`Verified ${pages.size} HTML routes, ${indexed.length} canonical pages, all internal references, sitemap, locale clusters, shared navigation, design-token coverage and social images.`);

import {storySlides as classic,chapterOpenings as classicOpenings,emphases as baseEmphases,type StorySlide} from './story';
import {compactTranslations as exampleTranslations,compactCopy as exampleCopy} from './compact-copy';
const opening=['How to architect an AI-first company','Start with business outcomes. Design the management, team and systems that deliver them.','AI-first company'];
export const chapterOpenings=classicOpenings.map((c,i)=>i===0?opening:c);
// Conservative edit of the classic: retain every framework step and chapter.
// These five beats repeat information retained in their chapter assemblies.
const omitted=new Set([19,32,42,44,49]);
const additions=exampleCopy.filter(b=>[120,123,125,126].includes(b.concept));
export const storySlides:StorySlide[]=classic.filter(s=>s.intro||!omitted.has(s.concept)).flatMap(s=>{
 const beat={...s};
 if(s.intro&&s.chapter===0){beat.title=opening[0];beat.line=opening[1];}
 if(s.concept===27)return [beat,...additions.map(b=>({id:0,concept:b.concept,chapter:4,title:b.title,line:b.line,assembly:b.concept===123,intro:false}))];
 return [beat];
}).map((s,i)=>({...s,id:i+1}));
export const compactDetails:Record<number,{mode:string}>={120:{mode:'prompt'},123:{mode:'build'},125:{mode:'evals'},126:{mode:'repair'}};
export const compactTranslations=exampleTranslations;
export const emphases:Record<number,string>={...baseEmphases,...Object.fromEntries(additions.map(b=>[b.concept,b.emphasis]))};
export const titleOverrides:Record<number,string>={};

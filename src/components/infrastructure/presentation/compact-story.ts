import {storySlides as classic,emphases as baseEmphases,type StorySlide} from './story';
import {compactTranslations as exampleTranslations,compactCopy as exampleCopy} from './compact-copy';
export const chapters=['The business thesis','The transformation process','Management','The transformation team','The company OS','The harness in practice','Memory & learning','Evidence & scale'];
export const chapterOpenings=[
 ['How to architect an AI-first company','Start with business outcomes. Connect the work. Build systems that can improve.','AI-first company'],
 ['Redesign the work. Then automate it.','The destination is clear. Now turn one valuable workflow into a repeatable result.','Then automate it.'],
 ['Give the transformation a management system.','A repeatable process needs a decision loop, clear ownership and a team to deliver it.','management system.'],
 ['The transformation team.','The management loop sets direction. Specialists turn each decision into working systems.','team.'],
 ['Build the shared company OS.','The team needs one foundation for context, execution, memory and evidence.','company OS.'],
 ['Inside the AI harness.','See how work runs, then use the same harness to build a workflow through MCP.','AI harness.'],
 ['Make the next run better informed.','Execution produces evidence. Memory keeps the knowledge and methods worth reusing.','better informed.'],
 ['Prove the result. Earn the right to scale.','Trace what happened, evaluate quality and measure the business outcome before expanding.','Earn the right to scale.'],
];
const sequences=[[1,2,3,34,40,41,140],[35,36,37,38,39],[4,5,6,7,8,9],[10,11,12,13,14,15],[16,17,20,51],[21,22,23,24,25,26,27,120,123,125,126],[28,29,30,31,33],[45,46,47,48,42,43,50]];
const additions=exampleCopy.filter(b=>[120,123,125,126].includes(b.concept));
const thesis={concept:140,title:'From a business goal to a company capability.',line:'Connect the tasks into a workflow. Make the workflow dependable as a system. Reuse proven systems across departments.',assembly:true,intro:false};
export const storySlides:StorySlide[]=sequences.flatMap((ids,chapter)=>{
 const opening=chapterOpenings[chapter];
 const intro={id:0,concept:0,chapter,title:opening[0],line:opening[1],assembly:false,intro:true};
 const beats=ids.map(concept=>{
  const example=additions.find(b=>b.concept===concept);
  const source=concept===140?thesis:example?{concept,title:example.title,line:example.line,assembly:concept===123,intro:false}:classic.find(s=>!s.intro&&s.concept===concept)!;
  return {...source,id:0,chapter};
 });
 return [intro,...beats];
}).map((s,i)=>({...s,id:i+1}));
export const compactDetails:Record<number,{mode:string}>={120:{mode:'prompt'},123:{mode:'build'},125:{mode:'evals'},126:{mode:'repair'}};
export const compactTranslations={...exampleTranslations};
export const emphases:Record<number,string>={...baseEmphases,...Object.fromEntries(additions.map(b=>[b.concept,b.emphasis])),140:'company capability.'};
export const titleOverrides:Record<number,string>={};

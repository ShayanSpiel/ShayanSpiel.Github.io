import {useEffect,useState} from 'react';
import {usePresentationLocale} from './Localization';
/** A presentation facsimile of the supplied Codex composer, not interactive controls. */
export default function CodexComposer(){
 const fa=usePresentationLocale()==='fa';
 const text=fa?'گردش‌کار استثناهای تحویل را برای واحد پشتیبانی بساز.':'Build the Support department’s delivery-exception workflow.';
 const [shown,setShown]=useState(text.length);
 useEffect(()=>{const reduced=matchMedia('(prefers-reduced-motion: reduce)');if(reduced.matches){setShown(text.length);return;}setShown(0);let count=0;const timer=setInterval(()=>{count=Math.min(text.length,count+2);setShown(count);if(count===text.length)clearInterval(timer);},30);const stop=()=>{if(reduced.matches){clearInterval(timer);setShown(text.length);}};reduced.addEventListener('change',stop);return()=>{clearInterval(timer);reduced.removeEventListener('change',stop);};},[text]);
 return <div className="codex-reference-composer" dir={fa?'rtl':'ltr'} aria-label={text}><div className="codex-reference-prompt"><span className="codex-prompt-reserve" aria-hidden="true">{text}</span><strong aria-hidden="true">{text.slice(0,shown)}{shown<text.length&&<i className="codex-typing-caret"/>}</strong></div><div className="codex-reference-controls" aria-hidden="true"><span className="codex-add">＋</span><span className="codex-access"><svg viewBox="0 0 24 24"><path d="M12 2 21 6v7c0 5-9 9-9 9S3 18 3 13V6Z"/><path d="M12 7v6m0 3v1"/></svg>{fa?'دسترسی کامل':'Full access'}</span><span className="codex-model"><i/>GPT-6 Astra <em>Medium</em><small>⌄</small></span><svg className="codex-mic" viewBox="0 0 24 24"><rect x="9" y="2" width="6" height="13" rx="3"/><path d="M5 11v2a7 7 0 0 0 14 0v-2M12 20v3"/></svg><span className="codex-send"><svg viewBox="0 0 24 24"><path d="m4 11 8-8 8 8M12 3v19"/></svg></span></div></div>;
}

import { buildExampleCopy } from './build-example-copy';
import { createContext, useContext, type ReactNode } from 'react';
import { persian } from './persian';
import { compactTranslations } from './compact-story';
export type PresentationLocale = 'en' | 'fa';
const BuildExampleContext = createContext(false);
const LocaleContext = createContext<PresentationLocale>('en');
export function PresentationLocaleProvider({locale,children,buildExample=false}:{locale:PresentationLocale;children:ReactNode;buildExample?:boolean}) {return <LocaleContext.Provider value={locale}><BuildExampleContext.Provider value={buildExample}>{children}</BuildExampleContext.Provider></LocaleContext.Provider>;}
export function usePresentationLocale(){return useContext(LocaleContext);}
export function translate(text:string,locale:PresentationLocale){
 if(locale!=='fa')return text;
 const key=text.trim();
 if(compactTranslations[key]||persian[key])return text.replace(key,compactTranslations[key]||persian[key]);
 return text;
}
export function LocalizedContent({value}:{value:ReactNode}){const locale=usePresentationLocale();const buildExample=useContext(BuildExampleContext);if(typeof value!=='string')return value;const replacement=buildExample?buildExampleCopy[value.trim()]:undefined;return replacement?value.replace(value.trim(),replacement[locale==='fa'?1:0]):translate(value,locale);}

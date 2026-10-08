import { createContext, useContext, type ReactNode } from 'react';
import { persian } from './persian';
export type PresentationLocale = 'en' | 'fa';
const LocaleContext = createContext<PresentationLocale>('en');
export function PresentationLocaleProvider({locale,children}:{locale:PresentationLocale;children:ReactNode}) {return <LocaleContext.Provider value={locale}>{children}</LocaleContext.Provider>;}
export function usePresentationLocale(){return useContext(LocaleContext);}
export function translate(text:string,locale:PresentationLocale){
 if(locale!=='fa')return text;
 const key=text.trim();
 if(persian[key])return text.replace(key,persian[key]);
 return text;
}
export function LocalizedContent({value}:{value:ReactNode}){const locale=usePresentationLocale();return typeof value==='string'?translate(value,locale):value;}

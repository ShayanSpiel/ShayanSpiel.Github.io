/** Crisp, consistent vector interface icons: 24px grid, 1.6px stroke. */
import { iconPaths } from './world-icon-paths';

export function Icon({name}:{name:string}) { return <svg className="bx world-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={iconPaths[name] ?? iconPaths.cube}/></svg>; }

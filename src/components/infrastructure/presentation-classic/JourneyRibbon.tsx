import { useLayoutEffect, useRef } from 'react';
import type { Scene } from './scenes';
export const RIBBON_DESIGN = { bodyWidth: 6.624, headWidth: 15.12, headLength: 18.72, dash: 19, gap: 14, blue: '#3a80ed', future: '#71819b' };
export function sceneGeometry(scene:Scene){
 const assembly=!!scene.kind&&!['thesis','chapter','dashboard'].includes(scene.kind);
 if(assembly){const w=Math.max(1120,...scene.tiles.map(t=>t.x+t.w)),h=Math.max(scene.kind==='management'?640:0,scene.kind==='finale'?860:0,...scene.tiles.map(t=>t.y+t.h+20));const scale=Math.min(1500/w,700/h);return {scale,x:(1680-w*scale)/2,y:175+(700-h*scale)/2,w,h};}
 const w=1120,h=460,scale=940/w;return {scale,x:1180-w*scale/2,y:455-h*scale/2,w,h};
}
export default function JourneyRibbon({ scene, index, leaving }: {
    scene: Scene;
    index: number;
    leaving: boolean;
}) {
    const incoming = useRef<SVGPathElement>(null), outgoing = useRef<SVGPathElement>(null), solid = useRef<SVGPathElement>(null), head = useRef<SVGPolygonElement>(null), wake = useRef<SVGPathElement>(null), frame = useRef(0);
    const assembly=!!scene.kind&&!['thesis','chapter','dashboard'].includes(scene.kind);
    const g=sceneGeometry(scene),node=scene.tiles[0],last=scene.tiles[scene.tiles.length-1];
    const left=g.x+node.x*g.scale,right=left+node.w*g.scale,y=g.y+(node.y+node.h*.5)*g.scale;
    const top=g.y+node.y*g.scale,cx=left+node.w*g.scale/2;
    const fromX=assembly?g.x+(last.x+last.w*.5)*g.scale:right,fromY=assembly?g.y+(last.y+last.h)*g.scale:y;
    const entry=assembly?`M 840 174 C 840 188 ${cx} 190 ${cx} ${top}`:`M 590 800 C 710 875 850 810 ${left-90} ${y+100} C ${left-100} ${y+40} ${left-55} ${y} ${left} ${y}`;
    const exit=`M ${fromX} ${fromY} C ${fromX+100} ${Math.min(860,fromY+110)} 1530 870 1640 835 C 1710 810 1750 780 1790 760`;
    useLayoutEffect(() => {
        cancelAnimationFrame(frame.current);
        const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
        let start = performance.now();
        const update = (now: number) => {
            if (!incoming.current || !outgoing.current || !solid.current || !head.current || !wake.current)
                return;
            const elapsed = now - start, path = leaving ? outgoing.current : incoming.current;
            const duration = leaving ? 450 : 800, t = reduce ? 1 : Math.min(1, elapsed / duration), u = 1 - Math.pow(1 - Math.max(0, t), 3), length = path.getTotalLength(), tipLength = Math.max(35, length * u), baseLength = Math.max(0, tipLength - RIBBON_DESIGN.headLength * 1.9), tip = path.getPointAtLength(tipLength), base = path.getPointAtLength(baseLength), ahead = path.getPointAtLength(Math.min(length, baseLength + 1)), dx = ahead.x - base.x, dy = ahead.y - base.y, norm = Math.hypot(dx, dy) || 1, nx = -dy / norm * RIBBON_DESIGN.headWidth * .95, ny = dx / norm * RIBBON_DESIGN.headWidth * .95;
            solid.current.setAttribute('d', path.getAttribute('d')!);
            solid.current.style.strokeDasharray = `${baseLength} ${length}`;
            wake.current.setAttribute('d', path.getAttribute('d')!);
            wake.current.style.strokeDasharray = `${baseLength} ${length}`;
            head.current.setAttribute('points', `${tip.x},${tip.y} ${base.x + nx},${base.y + ny} ${base.x - nx},${base.y - ny}`);
            if (!reduce && elapsed < duration)
                frame.current = requestAnimationFrame(update);
        };
        frame.current = requestAnimationFrame(update);
        return () => cancelAnimationFrame(frame.current);
    }, [index, entry, exit, leaving]);
    return <svg className="deck-signature-ribbon" viewBox="0 0 1680 940" aria-hidden="true" data-signature="film-v8-planar-ribbon"><defs><filter id="ribbon-shadow"><feDropShadow dx="0" dy="5" stdDeviation="4" floodColor="#030814" floodOpacity=".6"/></filter></defs><g className="ribbon-projection"><path ref={incoming} d={entry} className="ribbon-future"/><path ref={outgoing} d={exit} className="ribbon-future"/><path ref={wake} className="ribbon-wake"/><path ref={solid} className="ribbon-solid"/><polygon ref={head} className="ribbon-arrow"/><g transform={`translate(${assembly?cx:left} ${assembly?top:y})`} className="ribbon-arrival"><circle r="64.6"/><circle r="43.7"/><circle r="17.1"/></g></g></svg>;
}

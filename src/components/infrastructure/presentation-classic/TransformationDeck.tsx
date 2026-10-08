import { LocalizedContent, PresentationLocaleProvider, usePresentationLocale, translate, type PresentationLocale } from './Localization';
import { useEffect, useLayoutEffect, useRef, useState, type CSSProperties } from 'react';
import { storySlides as slides, chapterOpenings, titleOverrides, emphases } from './story';
import { chapters, sceneFor, type Tile, type Edge } from './scenes';
import { Icon } from '../WorldIcons';
import './presentation.css';
import './polish.css';
import ComponentSurface from './ComponentSurface';
import JourneyRibbon, { sceneGeometry } from './JourneyRibbon';
import { SPIELOS_MARK_D } from '../../../lib/spielos-mark';
function Title({ id, text, introChapter }: {
    id: number;
    text: string;
    introChapter?: number;
}) {
    const locale = usePresentationLocale();
    text = translate(text, locale);
    const emphasis = translate((introChapter === undefined ? emphases[id] : chapterOpenings[introChapter][2]) || '', locale);
    if (!emphasis || !text.includes(emphasis))
        return <><LocalizedContent value={text}/></>;
    const start = text.indexOf(emphasis);
    return <><LocalizedContent value={text.slice(0, start)}/><em><LocalizedContent value={emphasis}/></em><LocalizedContent value={text.slice(start + emphasis.length)}/></>;
}
function ChapterLead({ chapter }: {
    chapter: number;
}) {
    if (chapter === 0)
        return <svg className="deck-chapter-mark deck-chapter-mark--0" viewBox="0 0 24 24" aria-hidden="true"><path d={SPIELOS_MARK_D}/></svg>;
    const shapes = [
        '',
        'M12 3a9 9 0 1 1-8.7 6.7M3 3v7h7 M12 7v5l4 3',
        'M12 3v6M4 13v-4h16v4M4 17v4M12 13v8M20 17v4M2 13h4v4H2zM10 9h4v4h-4zM18 13h4v4h-4z',
        'm2 7 10-5 10 5-10 5zM2 12l10 5 10-5M2 17l10 5 10-5',
        'M8 5h8v14H8zM11 9l3 3-3 3M4 8H1v8h3M20 8h3v8h-3M8 2v3M16 2v3M8 19v3M16 19v3',
        'M3 6c0-5 18-5 18 0s-18 5-18 0v12c0 5 18 5 18 0V6M3 12c0 5 18 5 18 0',
        'M2 3h6v6H2zM16 15h6v6h-6zM16 3h6v6h-6zM8 6h8M19 9v6M5 9v9h11',
        'M12 2v6M3 15v-4h18v4M1 15h4v6H1zM10 15h4v6h-4zM19 15h4v6h-4zM12 11v4',
        'M2 21V3M2 21h20M5 16l4-6 4 3 7-9M5 19v-3M9 19v-6M13 19v-3M17 19v-7M21 19V8',
        'M4 19l6-6 4 2 7-12M15 3h6v6M3 21h18',
    ];
    return <svg className={`deck-chapter-mark deck-chapter-diagram deck-chapter-mark--${chapter}`} viewBox="0 0 24 24" aria-hidden="true"><path d={shapes[chapter]}/></svg>;
}
function FinaleClosure() {
    const video = useRef<HTMLVideoElement>(null);
    const [finished, setFinished] = useState(false);
    useEffect(() => {
        const media = matchMedia('(prefers-reduced-motion: reduce)');
        const sync = () => {
            if (media.matches) {
                video.current?.pause();
                setFinished(true);
            }
            else {
                setFinished(false);
                if (video.current) {
                    video.current.currentTime = 0;
                    video.current.play().catch(() => setFinished(true));
                }
            }
        };
        sync();
        media.addEventListener('change', sync);
        return () => media.removeEventListener('change', sync);
    }, []);
    return <div className="deck-signature-film" data-finished={finished} aria-label="SpielOS. Thank you for your time.">
        <img className="deck-signature-still" src="/videos/spielos-signature-final.jpg" alt=""/>
        <video ref={video} muted playsInline preload="auto" onEnded={() => setFinished(true)} onError={() => setFinished(true)} aria-hidden="true"><source src="/videos/spielos-signature.mp4" type="video/mp4"/></video>
        <p><LocalizedContent value={"Thank you for your time."}/></p>
    </div>;
}
function connector(a: Tile, b: Tile, mode?: string) {
    if (a.id === 'os' && ['sales', 'support', 'marketing', 'finance', 'operations'].includes(b.id)) {
        const x = Math.max(a.x + 25, Math.min(a.x + a.w - 25, b.x + b.w / 2));
        return `M ${x} ${a.y + a.h} C ${x} ${a.y + a.h + 22} ${b.x + b.w / 2} ${b.y - 22} ${b.x + b.w / 2} ${b.y}`;
    }
    if (b.id === 'providers') {
        const x = a.x + a.w / 2;
        return `M ${x} ${a.y + a.h} C ${x} ${a.y + a.h + 35} ${x} ${b.y - 35} ${x} ${b.y}`;
    }
    const ax = a.x + a.w / 2, ay = a.y + a.h / 2, bx = b.x + b.w / 2, by = b.y + b.h / 2;
    if (mode === 'return')
        return `M ${ax} ${a.y + a.h} V 352 Q ${ax} 375 ${ax - 23} 375 H ${bx + 23} Q ${bx} 375 ${bx} 352 V ${b.y + b.h}`;
    if (Math.abs(bx - ax) > Math.abs(by - ay) * 1.45) {
        const sign = bx > ax ? 1 : -1, x = ax + sign * a.w / 2, ex = bx - sign * b.w / 2, mid = (x + ex) / 2;
        return `M ${x} ${ay} C ${mid} ${ay} ${mid} ${by} ${ex} ${by}`;
    }
    const sign = by > ay ? 1 : -1, y = ay + sign * a.h / 2, ey = by - sign * b.h / 2, mid = (y + ey) / 2;
    return `M ${ax} ${y} C ${ax} ${mid} ${bx} ${mid} ${bx} ${ey}`;
}
function Connections({ tiles, edges, width, height }: {
    tiles: Tile[];
    edges: Edge[];
    width: number;
    height: number;
}) {
    return <svg className="deck-connections" viewBox={`0 0 ${width} ${height}`} aria-hidden="true"><defs><marker id="deck-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M 1 1 L 9 5 L 1 9" fill="none" stroke="var(--primary)" strokeWidth="1.6"/></marker></defs><LocalizedContent value={edges.map(([from, to, mode, route], i) => { const a = tiles.find(t => t.id === from), b = tiles.find(t => t.id === to); if (!a || !b)
        return null; const d = route || connector(a, b, mode); const coordinates = d.match(/-?\d+(?:\.\d+)?/g)?.map(Number) || []; return <g key={`${from}-${to}`} data-guide-edge-from={from} data-guide-edge-to={to} style={{ '--draw-delay': `${120 + i * 85}ms` } as CSSProperties}><path className="deck-future" d={d}/><path className="deck-line" d={d} pathLength="1" markerEnd="url(#deck-arrow)" markerStart={mode === 'both' ? 'url(#deck-arrow)' : undefined}/><circle className="deck-connection-port" cx={coordinates[0]} cy={coordinates[1]} r="3.5"/><LocalizedContent value={(!route || mode === 'circle') && <circle className="deck-connection-port" cx={coordinates.at(-2)} cy={coordinates.at(-1)} r="3.5"/>}/></g>; })}/></svg>;
}
function Deck() {
    const locale = usePresentationLocale();
    const rtl = locale === 'fa';
    const t = (text: string) => translate(text, locale);
    const [index, setIndex] = useState(0), [fullscreen, setFullscreen] = useState(false), [scale, setScale] = useState(1), [leaving, setLeaving] = useState(false);
    const root = useRef<HTMLDivElement>(null), viewport = useRef<HTMLDivElement>(null), rects = useRef(new Map<string, DOMRect>()), lastInput = useRef(0), touch = useRef({ x: 0, y: 0 }), goRef = useRef<(i: number, history?: boolean) => void>(() => { });
    const transition = useRef<ReturnType<typeof setTimeout> | null>(null);
    const slide = slides[index], scene = slide.intro || slide.concept === 50 ? { tiles: [], edges: [], kind: 'chapter' } : sceneFor(slide.concept), chapterSlides = slides.filter(s => s.chapter === slide.chapter), geometry = sceneGeometry(scene);
    function go(next: number, history = true) {
        next = Math.max(0, Math.min(slides.length - 1, next));
        if (!history && transition.current) {
            clearTimeout(transition.current);
            transition.current = null;
            setLeaving(false);
        }
        if (next === indexRef.current || transition.current)
            return;
        const commit = () => {
            rects.current.clear();
            root.current?.querySelectorAll<HTMLElement>('[data-node]').forEach(el => rects.current.set(el.dataset.node!, el.getBoundingClientRect()));
            setIndex(next);
            setLeaving(false);
            transition.current = null;
            if (history)
                window.history.pushState(null, '', `#slide-${next + 1}`);
        };
        if (!history || matchMedia('(prefers-reduced-motion: reduce)').matches)
            commit();
        else {
            setLeaving(true);
            transition.current = setTimeout(commit, 650);
        }
    }
    goRef.current = go;
    useLayoutEffect(() => {
        const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
        root.current?.querySelectorAll<HTMLElement>('[data-node]').forEach(el => {
            const previous = rects.current.get(el.dataset.node!);
            if (reduced)
                return;
            const next = el.getBoundingClientRect();
            if (previous) {
                el.animate([{ transform: `translate(${(previous.x - next.x) / (scale * geometry.scale)}px, ${(previous.y - next.y) / (scale * geometry.scale)}px) scale(${previous.width / next.width},${previous.height / next.height})`, opacity: 1 }, { transform: 'translate(0,0) scale(1)', opacity: 1 }], { duration: 780, easing: 'cubic-bezier(.22,1,.36,1)' });
            }
            else
                el.animate([{ opacity: 0, transform: 'translateY(22px) scale(.97)' }, { opacity: 1, transform: 'translateY(0) scale(1)' }], { duration: 760, delay: slide.assembly ? 80 + Math.max(0, parseFloat(el.style.top)) / Math.max(1, geometry.h) * 320 : 100, easing: 'cubic-bezier(.22,1,.36,1)', fill: 'backwards' });
        });
        rects.current.clear();
    }, [index, scale]);
    useEffect(() => {
        document.documentElement.classList.add('transformation-deck-active');
        const hash = () => { const m = location.hash.match(/^#slide-(\d+)$/); goRef.current(m ? Number(m[1]) - 1 : 0, false); };
        hash();
        const fit = () => { setScale(Math.min(window.innerWidth / 1680, window.innerHeight / 940)); };
        const observer = new ResizeObserver(fit);
        if (root.current)
            observer.observe(root.current);
        fit();
        const key = (e: KeyboardEvent) => {
            if ((e.target as HTMLElement).closest('input,textarea,select,[contenteditable=true]') || (e.key === ' ' && (e.target as HTMLElement).closest('button,a')))
                return;
            if ([rtl ? 'ArrowLeft' : 'ArrowRight', 'ArrowDown', 'PageDown', ' '].includes(e.key)) {
                e.preventDefault();
                goRef.current(indexRef.current + 1);
            }
            if ([rtl ? 'ArrowRight' : 'ArrowLeft', 'ArrowUp', 'PageUp'].includes(e.key)) {
                e.preventDefault();
                goRef.current(indexRef.current - 1);
            }
            if (e.key === 'Home') {
                e.preventDefault();
                goRef.current(0);
            }
            if (e.key === 'End') {
                e.preventDefault();
                goRef.current(slides.length - 1);
            }
            if (e.key.toLowerCase() === 'f')
                toggleFullscreen();
        };
        const wheel = (e: WheelEvent) => {
            if (Math.abs(e.deltaY) < 12 || e.ctrlKey)
                return;
            e.preventDefault();
            const now = performance.now();
            if (now - lastInput.current < 900)
                return;
            lastInput.current = now;
            goRef.current(indexRef.current + (e.deltaY > 0 ? 1 : -1));
        };
        const fs = () => setFullscreen(Boolean(document.fullscreenElement));
        window.addEventListener('keydown', key);
        window.addEventListener('popstate', hash);
        window.addEventListener('hashchange', hash);
        root.current?.addEventListener('wheel', wheel, { passive: false });
        document.addEventListener('fullscreenchange', fs);
        const host = root.current;
        return () => {
            if (transition.current)
                clearTimeout(transition.current);
            observer.disconnect();
            document.documentElement.classList.remove('transformation-deck-active');
            window.removeEventListener('keydown', key);
            window.removeEventListener('popstate', hash);
            window.removeEventListener('hashchange', hash);
            host?.removeEventListener('wheel', wheel);
            document.removeEventListener('fullscreenchange', fs);
        };
    }, []);
    const indexRef = useRef(0);
    indexRef.current = index;
    async function toggleFullscreen() {
        try {
            if (document.fullscreenElement)
                await document.exitFullscreen();
            else
                await root.current?.requestFullscreen();
        }
        catch {
            setFullscreen(false);
        }
    }
    return <div ref={root} className="transformation-deck" data-theme="blue-dark" lang={locale} dir={rtl ? 'rtl' : 'ltr'} data-slide={slide.id} data-slide-count={slides.length} data-concept={slide.concept} data-intro={slide.intro} data-chapter={slide.chapter} data-assembly={slide.assembly} data-leaving={leaving} onTouchStart={e => { touch.current = { x: e.changedTouches[0].clientX, y: e.changedTouches[0].clientY }; }} onTouchEnd={e => {
            const dx = touch.current.x - e.changedTouches[0].clientX, dy = touch.current.y - e.changedTouches[0].clientY;
            if (Math.max(Math.abs(dx), Math.abs(dy)) > 55)
                go(index + (Math.abs(dx) > Math.abs(dy) ? (dx > 0 ? 1 : -1) * (rtl ? -1 : 1) : dy > 0 ? 1 : -1));
        }}>
<nav className="deck-editions" aria-label={rtl?'نسخه و زبان':'Edition and language'}><a href={`/${rtl?'fa/':''}ai-transformation/`}>{rtl?'نسخهٔ فشرده':'Compact edition'}</a><span>·</span><a href={`/${rtl?'':'fa/'}ai-transformation-classic/`} lang={rtl?'en':'fa'}>{rtl?'English':'فارسی'}</a></nav>
 <button className="deck-fullscreen" onClick={toggleFullscreen} aria-label={t(fullscreen ? 'Exit fullscreen' : 'Enter fullscreen')} title={t('Fullscreen · F')}><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d={fullscreen ? 'M4 9h5V4m6 0v5h5M4 15h5v5m6 0v-5h5' : 'M9 4H4v5m11-5h5v5M4 15v5h5m6 0h5v-5'}/></svg></button>
 <div className="deck-canonical-frame" style={{ transform: `translate(-50%, -50%) scale(${scale})` }} data-guide-design-width="1680" data-guide-design-height="940" data-guide-geometry-valid={scene.edges.every(([a, b]) => scene.tiles.some(t => t.id === a) && scene.tiles.some(t => t.id === b))} data-guide-geometry-resolved="true">
 <LocalizedContent value={slide.intro && <ChapterLead chapter={slide.chapter}/>}/>
 <LocalizedContent value={!slide.intro && slide.concept !== 50 && <JourneyRibbon scene={scene} index={index} leaving={leaving}/>}/>
 <main className="deck-slide" aria-label={`${t(chapters[slide.chapter])}, ${rtl?'اسلاید':'slide'} ${slide.id} / ${slides.length}`}>
 <header className="deck-heading" key={slide.id}><h1><Title id={slide.concept} introChapter={slide.intro ? slide.chapter : undefined} text={titleOverrides[slide.concept] || slide.title}/></h1><p><LocalizedContent value={slide.line}/></p></header>
 <LocalizedContent value={!slide.intro && <div ref={viewport} className="deck-visual-viewport"><div className={`deck-artboard deck-artboard--${scene.kind || 'primitive'}`} style={{ left: rtl ? 1680 - geometry.x - geometry.w * geometry.scale : geometry.x, top: geometry.y, width: geometry.w, height: geometry.h, transform: `scale(${geometry.scale})` }}>
 <Connections tiles={scene.tiles} edges={scene.edges} width={geometry.w} height={geometry.h}/>
 <LocalizedContent value={scene.tiles.map(node => <ComponentSurface key={node.id} node={rtl ? {...node,x:geometry.w-node.x-node.w} : node} kind={scene.kind}/>)}/>
 <LocalizedContent value={scene.kind === 'finale' && <div className="deck-cycle-rail"><LocalizedContent value={"Goal "}/><span><LocalizedContent value={"\u2192"}/></span><LocalizedContent value={" Observe "}/><span><LocalizedContent value={"\u2192"}/></span><LocalizedContent value={" Decide "}/><span><LocalizedContent value={"\u2192"}/></span><LocalizedContent value={" Act "}/><span><LocalizedContent value={"\u2192"}/></span><LocalizedContent value={" Evaluate "}/><span><LocalizedContent value={"\u21BA"}/></span></div>}/>
 </div></div>}/>
 </main>
 <LocalizedContent value={slide.concept === 50 && <FinaleClosure />}/>
 </div>
 <div className="deck-rotate"><span><Icon name="refresh"/></span><p><LocalizedContent value={"Turn your screen."}/></p><small><LocalizedContent value={"This presentation is composed for landscape."}/></small></div>
 <nav className="deck-progress" aria-label={t('Presentation navigation')}><div className="deck-chapter-dots"><LocalizedContent value={chapters.map((name, c) => <button key={name} aria-label={`${rtl?'فصل':'Chapter'} ${c}: ${t(name)}`} title={t(name)} aria-current={c === slide.chapter ? 'step' : undefined} className={c < slide.chapter ? 'complete' : ''} onClick={() => go(slides.findIndex(s => s.chapter === c))}/>)}/></div><span className="deck-progress-divider"/><div className="deck-slide-dots"><LocalizedContent value={chapterSlides.map(s => <button key={s.id} aria-label={`${rtl?'اسلاید':'Slide'} ${s.id}: ${t(s.title)}`} title={t(s.title)} aria-current={s.id === slide.id ? 'step' : undefined} className={`${s.id < slide.id ? 'complete' : ''} ${s.assembly ? 'assembly-dot' : ''}`} onClick={() => go(s.id - 1)}/>)}/></div><small><LocalizedContent value={String(slide.id).padStart(2, '0')}/><LocalizedContent value={" / "}/><LocalizedContent value={slides.length}/></small></nav>
 <span className="deck-announcement" aria-live="polite" aria-atomic="true"><LocalizedContent value={chapters[slide.chapter]}/><LocalizedContent value={". Slide "}/><LocalizedContent value={slide.id}/><LocalizedContent value={" of "}/><LocalizedContent value={slides.length}/><LocalizedContent value={". "}/><LocalizedContent value={titleOverrides[slide.concept] || slide.title}/></span>
 <noscript><div className="deck-transcript"><LocalizedContent value={slides.map(s => <section key={s.id}><h2><LocalizedContent value={s.title}/></h2><p><LocalizedContent value={s.line}/></p></section>)}/></div></noscript>
 </div>;
}

export default function TransformationDeck({locale='en'}:{locale?:PresentationLocale}) { return <PresentationLocaleProvider locale={locale}><Deck/></PresentationLocaleProvider>; }

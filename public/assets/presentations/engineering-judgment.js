/* Engineering the future of human judgment — deck runtime.
   Plain module: fits the 1680×940 stage, drives slides, fullscreen and deep links. */

const deck = document.querySelector(".ej-deck");
const frame = deck?.querySelector(".deck-canonical-frame");
const slides = [...document.querySelectorAll(".ej-slide")];
const dots = [...document.querySelectorAll(".deck-progress button")];
const counter = document.querySelector(".deck-progress small");
const live = document.getElementById("ej-live");

if (deck && frame && slides.length) {
  const STAGE_W = 1680;
  const STAGE_H = 940;
  let index = 0;

  const fit = () => {
    const header = document.querySelector(".kw-site-header");
    const top = deck.classList.contains("is-fullscreen") || document.fullscreenElement === deck
      ? 0
      : Math.round(header?.getBoundingClientRect().bottom ?? 0);
    deck.style.setProperty("--ej-top", `${top}px`);
    deck.style.setProperty("--ej-height", `${Math.max(320, window.innerHeight - top)}px`);
    deck.classList.toggle("is-fullscreen", document.fullscreenElement === deck);
    const w = deck.clientWidth;
    const h = deck.clientHeight;
    const scale = Math.min(w / STAGE_W, h / STAGE_H);
    /* The stage keeps its 1680 design width and grows taller when the screen is
       taller than 16:9, so the composition fills the viewport instead of
       letterboxing. Slides are flex columns and absorb the extra height. */
    frame.style.height = `${Math.round(h / scale)}px`;
    frame.style.transform = `translate(-50%, -50%) scale(${scale})`;
    frame.style.setProperty("--ej-scale", scale);
  };

  const show = (next, { push = true } = {}) => {
    index = Math.max(0, Math.min(slides.length - 1, next));
    slides.forEach((slide, i) => {
      const on = i === index;
      slide.classList.toggle("is-active", on);
      slide.setAttribute("aria-hidden", on ? "false" : "true");
      slide.inert = !on;
    });
    dots.forEach((dot, i) => {
      if (i === index) dot.setAttribute("aria-current", "true");
      else dot.removeAttribute("aria-current");
    });
    if (counter) counter.textContent = `${String(index + 1).padStart(2, "0")} / ${String(slides.length).padStart(2, "0")}`;
    if (live) live.textContent = `Slide ${index + 1} of ${slides.length}: ${slides[index].getAttribute("aria-label") || ""}`;
    if (push) history.replaceState(null, "", `#slide-${index + 1}`);
  };

  const next = () => show(index + 1);
  const prev = () => show(index - 1);

  const fromHash = () => {
    const match = location.hash.match(/^#slide-(\d+)$/);
    return match ? Number(match[1]) - 1 : 0;
  };

  show(fromHash(), { push: false });
  fit();

  addEventListener("resize", fit);
  addEventListener("orientationchange", fit);
  document.querySelector(".kw-site-header")?.addEventListener("load", fit);

  document.addEventListener("fullscreenchange", () => {
    deck.classList.toggle("is-fullscreen", document.fullscreenElement === deck);
    fit();
  });

  document.querySelectorAll("[data-ej-next]").forEach((button) => button.addEventListener("click", next));
  document.querySelectorAll("[data-ej-prev]").forEach((button) => button.addEventListener("click", prev));
  dots.forEach((dot, i) => dot.addEventListener("click", () => show(i)));
  document.querySelector(".deck-restart")?.addEventListener("click", () => show(0));

  const fullscreenButton = document.querySelector(".deck-fullscreen");
  fullscreenButton?.addEventListener("click", () => {
    if (document.fullscreenElement) document.exitFullscreen();
    else deck.requestFullscreen?.().catch(() => {});
  });

  addEventListener("keydown", (event) => {
    if (event.defaultPrevented || event.metaKey || event.ctrlKey || event.altKey) return;
    const key = event.key;
    if (event.target instanceof Element &&
        event.target.closest("input, textarea, select, [contenteditable], button, a") &&
        (key === " " || key === "Spacebar")) return;
    if (key === "ArrowRight" || key === "PageDown" || key === " " || key === "Spacebar") {
      event.preventDefault();
      next();
    } else if (key === "ArrowLeft" || key === "PageUp") {
      event.preventDefault();
      prev();
    } else if (key === "Home") {
      event.preventDefault();
      show(0);
    } else if (key === "End") {
      event.preventDefault();
      show(slides.length - 1);
    } else if (key === "f" || key === "F") {
      fullscreenButton?.click();
    }
  });

  let wheelAt = 0;
  addEventListener(
    "wheel",
    (event) => {
      if (Math.abs(event.deltaY) < 24) return;
      const now = Date.now();
      if (now - wheelAt < 650) return;
      wheelAt = now;
      if (event.deltaY > 0) next();
      else prev();
    },
    { passive: true }
  );

  let touchStart = null;
  addEventListener("touchstart", (event) => {
    touchStart = event.touches[0] ? { x: event.touches[0].clientX, y: event.touches[0].clientY } : null;
  }, { passive: true });
  addEventListener("touchend", (event) => {
    if (!touchStart || !event.changedTouches[0]) return;
    const dx = event.changedTouches[0].clientX - touchStart.x;
    const dy = event.changedTouches[0].clientY - touchStart.y;
    if (Math.abs(dx) > 55 && Math.abs(dx) > Math.abs(dy)) {
      if (dx < 0) next();
      else prev();
    }
    touchStart = null;
  }, { passive: true });

  addEventListener("hashchange", () => show(fromHash(), { push: false }));

  /* ring layer hover: highlight one layer band, its chips and spokes */
  document.querySelectorAll(".ej-stage--rings").forEach((stage) => {
    const set = (layer) => {
      if (layer == null) stage.removeAttribute("data-active-layer");
      else stage.setAttribute("data-active-layer", layer);
    };
    stage.querySelectorAll("[data-layer]").forEach((node) => {
      node.addEventListener("pointerenter", () => set(node.dataset.layer));
      node.addEventListener("pointerleave", () => set(null));
    });
    stage.querySelector(".ej-core")?.addEventListener("pointerenter", () => set(null));
  });
}

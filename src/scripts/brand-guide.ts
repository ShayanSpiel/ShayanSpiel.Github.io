const guide = document.querySelector<HTMLElement>("[data-brand-guide]");

if (guide) {
  document.documentElement.classList.add("brand-guide-active");
  document.body.classList.add("brand-guide-active");

  const slides = [...guide.querySelectorAll<HTMLElement>("[data-guide-slide]")];
  const dots = [...guide.querySelectorAll<HTMLButtonElement>("[data-guide-dot]")];
  const previousButtons = [...guide.querySelectorAll<HTMLButtonElement>("[data-guide-previous]")];
  const email = guide.querySelector<HTMLInputElement>("#brand-guide-email")!;
  const form = guide.querySelector<HTMLFormElement>(".guide-email-form")!;
  const error = guide.querySelector<HTMLElement>("[data-guide-error]")!;
  const currentLabel = guide.querySelector<HTMLElement>("[data-guide-current]")!;
  const fullscreenButton = guide.querySelector<HTMLButtonElement>("[data-guide-fullscreen]");
  let current = 0;
  let unlocked = false;
  let lastAdvance = 0;
  let touchStart = 0;
  const reducedMotion = matchMedia("(prefers-reduced-motion: reduce)");

  // The theme toggle lives in the shared site shell, while the guide is a
  // fixed presentation surface. Keep the surface in sync when a user changes
  // themes in another open page or tab without requiring a reload.
  const syncTheme = (value?: string | null) => {
    const nextTheme = value || document.documentElement.dataset.theme;
    if (nextTheme) guide.dataset.guideTheme = nextTheme;
  };
  syncTheme();
  addEventListener("storage", event => {
    if (event.key === "spielos.theme" && event.newValue) {
      document.documentElement.dataset.theme = event.newValue;
      syncTheme(event.newValue);
    }
  });
  new MutationObserver(() => syncTheme()).observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });

  const fitLayerSlides = () => {
    const narrowScene = matchMedia("(max-width: 60rem)").matches;
    guide.querySelectorAll<HTMLElement>(".guide-layer").forEach(layer => {
      const slide = layer.closest<HTMLElement>(".guide-slide");
      if (!slide) return;
      const styles = getComputedStyle(slide);
      const paddingStart = parseFloat(styles.paddingInlineStart);
      const paddingEnd = parseFloat(styles.paddingInlineEnd);
      const availableWidth = slide.clientWidth - paddingStart - paddingEnd;
      const availableHeight = slide.clientHeight - parseFloat(styles.paddingTop) - parseFloat(styles.paddingBottom);
      // The scene stays a widescreen artboard, but it must fit the actual
      // landscape viewport in both dimensions. Width-only fitting lets the
      // bottom rail sit on top of the diagram on short phones and tablets.
      const scale = narrowScene
        ? Math.min(availableWidth / layer.offsetWidth, availableHeight / layer.offsetHeight)
        : Math.min(1, availableWidth / layer.offsetWidth, availableHeight / layer.offsetHeight);
      const fittedScale = narrowScene ? Math.max(.2, scale) : Math.max(.25, scale);
      layer.style.setProperty("--guide-layer-scale", String(fittedScale));
      // Position the transformed artboard inside the slide's content box.
      // The old calculation centered against the full border box and then
      // added the slide's padding a second time, producing asymmetric gutters
      // (and scrollable overflow) on compact desktop frames.
      // The layer's normal-flow origin already includes the slide's inline
      // padding, so this is only the remaining content-box centering offset.
      const centeredLeft = (availableWidth - layer.offsetWidth * fittedScale) / 2;
      const left = Math.max(0, centeredLeft);
      layer.style.left = `${left}px`;
      if (narrowScene) {
        const top = parseFloat(styles.paddingTop) + Math.max(0, (availableHeight - layer.offsetHeight * fittedScale) / 2);
        layer.style.top = `${top}px`;
      } else {
        layer.style.removeProperty("top");
      }
      layer.style.transform = `scale(${fittedScale})`;
      layer.style.transformOrigin = "top left";
    });
  };

  const errorMessage = error.querySelector<HTMLElement>("[data-guide-error-message]");
  const showError = (message = form.dataset.invalidError, invalid = true) => {
    error.hidden = false;
    if (message && errorMessage) errorMessage.textContent = message;
    if (invalid) email.setAttribute("aria-invalid", "true");
    else email.removeAttribute("aria-invalid");
    email.focus({ preventScroll: true });
    guide.classList.remove("is-shaking");
    requestAnimationFrame(() => guide.classList.add("is-shaking"));
  };
  const unlock = () => {
    unlocked = true;
    error.hidden = true;
    email.removeAttribute("aria-invalid");
    guide.classList.add("is-unlocked");
    setSlide(1);
  };
  const setSlide = (index: number) => {
    if (index < 0 || index >= slides.length || (index > 0 && !unlocked)) {
      if (!unlocked) showError();
      return;
    }
    current = index;
    slides.forEach((slide, i) => {
      const active = i === current;
      slide.classList.toggle("is-active", active);
      slide.setAttribute("aria-hidden", String(!active));
      if (active) slide.querySelector<HTMLElement>("button, a, input")?.focus({ preventScroll: true });
    });
    dots.forEach((dot, i) => dot.setAttribute("aria-current", i + 1 === current ? "step" : "false"));
    previousButtons.forEach(button => { button.disabled = current === 0; });
    const activeSlide = slides[current];
    const displayNumber = activeSlide?.dataset.guideDisplayNumber ?? String(current);
    currentLabel.textContent = current === 0 ? "Access" : String(displayNumber).padStart(2, "0");
    guide.classList.toggle("is-opening", current <= 4);
    fitLayerSlides();
    dispatchEvent(new Event("brand-guide:refresh-diagrams"));
  };

  const setFullscreenState = () => {
    const active = document.fullscreenElement === guide;
    const icon = fullscreenButton?.querySelector<HTMLElement>("i");
    if (!fullscreenButton || !icon) return;
    icon.classList.toggle("bx-fullscreen", !active);
    icon.classList.toggle("bx-exit-fullscreen", active);
    const label = (active ? fullscreenButton.dataset.exitLabel : fullscreenButton.dataset.enterLabel) ?? "Fullscreen";
    fullscreenButton.setAttribute("aria-label", label);
    fullscreenButton.setAttribute("title", label);
  };

  fullscreenButton?.addEventListener("click", async () => {
    try {
      if (document.fullscreenElement) await document.exitFullscreen();
      else if (guide.requestFullscreen) await guide.requestFullscreen();
    } catch {
      // Fullscreen can be denied by the browser; the deck remains usable.
    } finally {
      setFullscreenState();
    }
  });
  document.addEventListener("fullscreenchange", setFullscreenState);
  // The reference's close slide offers the deck as a PDF. No guide PDF asset
  // exists yet, so the button hands the deck to the browser's print dialog —
  // a real, working action instead of a dead link.
  guide.querySelector<HTMLButtonElement>("[data-guide-pdf]")?.addEventListener("click", () => window.print());
  setSlide(0);
  const advance = (direction = 1) => {
    if (current === 0 && !unlocked) return showError();
    const next = Math.max(0, Math.min(slides.length - 1, current + direction));
    if (next === current && current === slides.length - 1) return;
    setSlide(next);
  };

  form.addEventListener("submit", async event => {
    event.preventDefault();
    if (!email.value.trim() || !email.checkValidity()) return showError();
    const submit = form.querySelector<HTMLButtonElement>('button[type="submit"]');
    if (!submit || submit.disabled) return;
    submit.disabled = true;
    submit.setAttribute("aria-busy", "true");
    try {
      const payload = Object.fromEntries(new FormData(form).entries());
      const response = await fetch(form.action, {
        method: "POST",
        body: JSON.stringify(payload),
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
      });
      if (!response.ok) throw new Error("Brand Guide signup failed");
      const result = await response.json().catch(() => null) as { success?: boolean | string } | null;
      if (result?.success !== true && result?.success !== "true") throw new Error("Brand Guide signup failed");
      unlock();
    } catch {
      showError(form.dataset.submitError, false);
    } finally {
      submit.disabled = false;
      submit.removeAttribute("aria-busy");
    }
  });
  email.addEventListener("input", () => {
    error.hidden = true;
    email.removeAttribute("aria-invalid");
    if (errorMessage && form.dataset.invalidError) errorMessage.textContent = form.dataset.invalidError;
  });
  guide.querySelectorAll<HTMLButtonElement>("[data-guide-next]").forEach(button => button.addEventListener("click", () => advance()));
  previousButtons.forEach(button => button.addEventListener("click", () => advance(-1)));
  dots.forEach((dot, index) => dot.addEventListener("click", () => unlocked ? setSlide(index + 1) : showError()));
  addEventListener("keydown", event => {
    if (!guide.isConnected || event.metaKey || event.ctrlKey || event.altKey) return;
    if (["ArrowDown", "ArrowRight", "PageDown", " ", "Enter"].includes(event.key) && document.activeElement !== email) { event.preventDefault(); advance(); }
    if (["ArrowUp", "ArrowLeft", "PageUp"].includes(event.key)) { event.preventDefault(); advance(-1); }
  });
  guide.addEventListener("wheel", event => {
    if (Math.abs(event.deltaY) < 16 || Date.now() - lastAdvance < 700) return;
    event.preventDefault(); lastAdvance = Date.now(); advance(event.deltaY > 0 ? 1 : -1);
  }, { passive: false });
  guide.addEventListener("touchstart", event => { touchStart = event.changedTouches[0]?.clientY ?? 0; }, { passive: true });
  guide.addEventListener("touchend", event => {
    const distance = touchStart - (event.changedTouches[0]?.clientY ?? touchStart);
    if (Math.abs(distance) > 55) advance(distance > 0 ? 1 : -1);
  }, { passive: true });
  addEventListener("resize", fitLayerSlides, { passive: true });

  const end = Date.now() + 14 * 24 * 60 * 60 * 1000;
  const tick = () => {
    const distance = Math.max(0, end - Date.now());
    const values = { days: Math.floor(distance / 86400000), hours: Math.floor(distance / 3600000) % 24, minutes: Math.floor(distance / 60000) % 60, seconds: Math.floor(distance / 1000) % 60 };
    Object.entries(values).forEach(([unit, value]) => {
      const output = guide.querySelector<HTMLElement>(`[data-countdown="${unit}"]`);
      if (output) output.textContent = String(value).padStart(2, "0");
    });
  };
  fitLayerSlides();
  tick(); setInterval(tick, 1000);
  if (reducedMotion.matches) guide.classList.add("prefers-reduced-motion");
}

/** The brand narrative: measured paths, a one-shot prompt demo, and native review form. */
const root = document.querySelector<HTMLElement>(".brand-page");
if (root) {
  const reducedMotion = matchMedia("(prefers-reduced-motion: reduce)");
  const clamp = (value: number) => Math.max(0, Math.min(1, value));
  const svgNS = "http://www.w3.org/2000/svg";
  type Journey = { el: HTMLElement; svg: SVGSVGElement; fill: SVGPathElement; tip: SVGGElement | null; length: number; top: number; height: number };
  let journeys: Journey[] = [];
  let scheduled = false;
  const diagram = root.querySelector<HTMLElement>("[data-system-diagram]");
  const systemSvg = diagram?.querySelector<SVGSVGElement>(".brand-system-svg");

  function measureSystem() {
    if (!diagram || !systemSvg) return;
    const box = diagram.getBoundingClientRect();
    const core = diagram.querySelector<HTMLElement>("[data-ai-core]");
    const lines = systemSvg.querySelector(".system-lines");
    if (!core || !lines || !box.width) return;
    systemSvg.setAttribute("viewBox", `0 0 ${box.width} ${box.height}`);
    const point = (el: Element, bottom: boolean) => {
      const rect = el.getBoundingClientRect();
      return { x: rect.left + rect.width / 2 - box.left, y: (bottom ? rect.bottom : rect.top) - box.top };
    };
    const coreTop = point(core, false), coreBottom = point(core, true);
    const routes: string[] = [];
    diagram.querySelectorAll("[data-input]").forEach((input, index) => {
      const a = point(input, true), b = { x: coreTop.x + (index - 1) * (document.dir === "rtl" ? -1 : 1) * core.clientWidth / 5, y: coreTop.y };
      const mid = (a.y + b.y) / 2;
      routes.push(`M${a.x},${a.y} C${a.x},${mid} ${b.x},${mid} ${b.x},${b.y}`);
    });
    const outputs = [...diagram.querySelectorAll("[data-output]")];
    const firstRowY = Math.min(...outputs.map(el => point(el, false).y));
    outputs.forEach((output, index) => {
      const b = point(output, false), a = { x: coreBottom.x + (index - 1.5) * 10, y: coreBottom.y };
      const trunkY = firstRowY - 30;
      if (b.y > firstRowY + 50) {
        const edge = b.x < box.width / 2 ? 2 : box.width - 2;
        routes.push(`M${a.x},${a.y} C${a.x},${trunkY - 35} ${edge},${trunkY - 35} ${edge},${trunkY} L${edge},${b.y - 24} Q${edge},${b.y - 10} ${b.x},${b.y - 10} L${b.x},${b.y}`);
      } else {
        routes.push(`M${a.x},${a.y} C${a.x},${trunkY - 30} ${b.x},${trunkY - 30} ${b.x},${b.y}`);
      }
    });
    lines.replaceChildren(...routes.map(d => {
      const path = document.createElementNS(svgNS, "path");
      path.setAttribute("d", d);
      path.setAttribute("vector-effect", "non-scaling-stroke");
      return path;
    }));
  }

  function measure() {
    journeys = [];
    root!.querySelectorAll<HTMLElement>("[data-journey]").forEach(el => {
      const from = root!.querySelector(el.dataset.from || ""), to = root!.querySelector(el.dataset.to || "");
      const svg = el.querySelector("svg"), fill = el.querySelector<SVGPathElement>(".journey-fill"), route = el.querySelector(".journey-route");
      if (!from || !to || !svg || !fill || !route) return;
      const wrapper = el.getBoundingClientRect(), a = from.getBoundingClientRect(), b = to.getBoundingClientRect();
      const start = a.bottom + 12, end = b.top - 12, height = Math.max(20, end - start), width = wrapper.width;
      const x1 = a.left + a.width / 2 - wrapper.left, x2 = b.left + b.width / 2 - wrapper.left;
      const direction = el.dataset.variant === "left" ? -1 : 1;
      const amplitude = Math.min(width * .2, 210) * direction;
      const right = x1 + amplitude * .65, left = x2 - amplitude;
      const d = `M${x1},0 C${x1},${height * .13} ${right},${height * .12} ${right},${height * .3} C${right},${height * .49} ${left},${height * .43} ${left},${height * .65} C${left},${height * .84} ${x2},${height * .82} ${x2},${height}`;
      svg.style.top = `${start - wrapper.top}px`;
      svg.style.height = `${height}px`;
      svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
      route.setAttribute("d", d); fill.setAttribute("d", d);
      const length = fill.getTotalLength();
      fill.style.strokeDasharray = String(length);
      journeys.push({ el, svg, fill, tip: el.querySelector(".journey-tip"), length, top: start + scrollY, height });
    });
    const hero = root!.querySelector<HTMLElement>(".brand-hero");
    const trash = root!.querySelector<HTMLElement>(".hero-trash .bx");
    if (hero && trash) {
      const previous = hero.style.getPropertyValue("--asset-fade");
      hero.style.setProperty("--asset-fade", "0");
      const target = trash.getBoundingClientRect();
      hero.querySelectorAll<HTMLElement>(".hero-discard").forEach(asset => {
        const box = asset.getBoundingClientRect();
        asset.style.setProperty("--discard-x", `${target.x + target.width / 2 - box.x - box.width / 2}px`);
        asset.style.setProperty("--discard-y", `${target.y + target.height / 2 - box.y - box.height / 2}px`);
      });
      hero.style.setProperty("--asset-fade", previous || "0");
    }
    measureSystem(); update();
  }

  function update() {
    scheduled = false;
    journeys.forEach(journey => {
      const progress = reducedMotion.matches ? 1 : clamp((scrollY + innerHeight * .72 - journey.top) / journey.height);
      journey.fill.style.strokeDashoffset = String(journey.length * (1 - progress));
      const point = journey.fill.getPointAtLength(journey.length * progress);
      journey.tip?.setAttribute("transform", `translate(${point.x} ${point.y})`);
      journey.el.classList.toggle("is-complete", progress >= 1);
    });
    const hero = root!.querySelector<HTMLElement>(".brand-hero");
    if (hero) hero.style.setProperty("--asset-fade", String(reducedMotion.matches ? 0 : clamp(-hero.getBoundingClientRect().top / (hero.offsetHeight * .85))));
  }
  const requestUpdate = () => { if (!scheduled) { scheduled = true; requestAnimationFrame(update); } };
  addEventListener("scroll", requestUpdate, { passive: true });
  addEventListener("resize", measure);
  reducedMotion.addEventListener("change", measure);
  new ResizeObserver(measure).observe(root);
  root.addEventListener("transitionend", event => { if ((event.target as HTMLElement)?.hasAttribute("data-aos")) measure(); });
  document.fonts.ready.then(measure);
  requestAnimationFrame(measure);

  const prompt = root.querySelector<HTMLElement>("[data-prompt-text]");
  const promptBox = root.querySelector<HTMLElement>("[data-prompt-hook]");
  if (prompt && promptBox) {
    const full = prompt.textContent || "";
    let started = false;
    const reveal = () => {
      if (started) return;
      started = true;
      promptBox.classList.add("is-prompt-ready");
      if (reducedMotion.matches) { prompt.textContent = full; return; }
      const startedAt = performance.now();
      const speed = parseFloat(getComputedStyle(root).getPropertyValue("--duration-fast")) / 4 || 30;
      const tick = (now: number) => {
        const length = reducedMotion.matches ? full.length : Math.floor((now - startedAt) / speed);
        prompt.textContent = full.slice(0, length);
        promptBox.classList.toggle("is-typing", length < full.length);
        if (length < full.length) requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
    };
    if (!reducedMotion.matches) prompt.textContent = "";
    const observer = new IntersectionObserver(entries => {
      if (entries.some(entry => entry.isIntersecting)) { observer.disconnect(); reveal(); }
    }, { threshold: .5 });
    observer.observe(promptBox);
  }

  const html = document.documentElement;
  const picker = root.querySelector<HTMLDetailsElement>(".brand-theme-picker");
  const palettes = [...root.querySelectorAll<HTMLButtonElement>("[data-theme-palette]")];
  const modes = [...root.querySelectorAll<HTMLButtonElement>("[data-theme-mode]")];
  const reflectTheme = () => {
    const current = html.dataset.theme || "gruvbox-dark";
    palettes.forEach(button => button.setAttribute("aria-pressed", String(current.replace(/-(light|dark)$/, "") === button.dataset.themePalette)));
    modes.forEach(button => button.setAttribute("aria-pressed", String(current.endsWith(`-${button.dataset.themeMode}`))));
  };
  const setTheme = (theme: string) => {
    html.dataset.theme = theme;
    try { localStorage.setItem("spielos.theme", theme); } catch { /* Private browsing: keep the session choice. */ }
    reflectTheme();
  };
  palettes.forEach(button => button.addEventListener("click", () => setTheme(`${button.dataset.themePalette}-${html.dataset.theme?.endsWith("-light") ? "light" : "dark"}`)));
  modes.forEach(button => button.addEventListener("click", () => setTheme(`${(html.dataset.theme || "gruvbox-dark").replace(/-(light|dark)$/, "")}-${button.dataset.themeMode}`)));
  new MutationObserver(reflectTheme).observe(html, { attributes: true, attributeFilter: ["data-theme"] });
  reflectTheme();
  document.addEventListener("click", event => { if (picker && !picker.contains(event.target as Node)) picker.open = false; });
  document.addEventListener("keydown", event => { if (event.key === "Escape" && picker?.open) { picker.open = false; picker.querySelector("summary")?.focus(); } });

  const dialog = document.querySelector<HTMLDialogElement>("#brand-review-dialog")!;
  const form = dialog.querySelector<HTMLFormElement>("#brand-review-form")!;
  const back = dialog.querySelector<HTMLButtonElement>("#brand-form-back")!;
  const next = dialog.querySelector<HTMLButtonElement>("#brand-form-next")!;
  const submit = dialog.querySelector<HTMLButtonElement>("#brand-form-submit")!;
  const submitLabel = submit.querySelector<HTMLElement>("[data-submit-label]")!;
  const submitText = submitLabel.textContent;
  const error = dialog.querySelector<HTMLElement>("#brand-form-error")!;
  const validation = dialog.querySelector<HTMLElement>("#brand-validation-error")!;
  const success = dialog.querySelector<HTMLElement>("#brand-form-success")!;
  const progress = dialog.querySelector<HTMLElement>(".brand-dialog__progress")!;
  const status = dialog.querySelector<HTMLElement>("#brand-form-status")!;
  const selected = dialog.querySelector<HTMLElement>("#selected-package")!;
  const selectedPrice = dialog.querySelector<HTMLElement>("#selected-price")!;
  const packageField = form.querySelector<HTMLInputElement>("#package-field")!;
  let current = 1, pending = false, completed = false;
  let lastTrigger: HTMLElement | null = null;
  const track = (name: string, detail: Record<string, unknown> = {}) => {
    (window as Window & { spielosTrack?: (name: string, detail: Record<string, unknown>) => void }).spielosTrack?.(name, detail);
  };
  const focusStep = () => {
    dialog.querySelector<HTMLElement>(".brand-dialog__fields")?.scrollTo(0, 0);
    form.querySelector<HTMLElement>(`[data-form-step="${current}"] input, [data-form-step="${current}"] textarea`)?.focus({ preventScroll: true });
  };
  function render() {
    form.querySelectorAll<HTMLElement>("[data-form-step]").forEach(step => { step.hidden = Number(step.dataset.formStep) !== current; });
    progress.querySelectorAll<HTMLElement>("[data-progress-step]").forEach(step => {
      const index = Number(step.dataset.progressStep);
      step.classList.toggle("is-current", index === current); step.classList.toggle("is-complete", index < current);
      if (index === current) step.setAttribute("aria-current", "step"); else step.removeAttribute("aria-current");
    });
    back.disabled = current === 1 || pending; next.hidden = current === 3; submit.hidden = current !== 3;
    submit.disabled = pending; next.disabled = pending;
    submit.setAttribute("aria-busy", String(pending));
    submitLabel.textContent = pending ? form.dataset.sendingMessage || "" : submitText;
    status.textContent = pending ? form.dataset.sendingMessage || "" : "";
  }
  function valid() {
    const fields = [...form.querySelectorAll<HTMLInputElement | HTMLTextAreaElement>(`[data-form-step="${current}"] [required]`)];
    const invalid = fields.filter(input => !input.checkValidity() || !input.value.trim());
    fields.forEach(input => {
      if (invalid.includes(input)) { input.setAttribute("aria-invalid", "true"); input.setAttribute("aria-errormessage", "brand-validation-error"); }
      else { input.removeAttribute("aria-invalid"); input.removeAttribute("aria-errormessage"); }
    });
    validation.textContent = form.dataset.validationMessage || "";
    validation.hidden = invalid.length === 0;
    invalid[0]?.focus();
    return invalid.length === 0;
  }
  document.querySelectorAll<HTMLButtonElement>(".js-brand-review").forEach(trigger => trigger.addEventListener("click", () => {
    lastTrigger = trigger;
    if (!pending) {
      selected.textContent = trigger.dataset.package || ""; selectedPrice.textContent = trigger.dataset.price || "";
      packageField.value = `${selected.textContent} — ${selectedPrice.textContent}`;
      if (completed) { form.reset(); completed = false; }
      current = 1; form.hidden = false; success.hidden = true; progress.hidden = false; error.hidden = true; validation.hidden = true;
      form.querySelectorAll("[aria-invalid]").forEach(input => input.removeAttribute("aria-invalid"));
    }
    render(); document.body.dataset.brandDialogOpen = "true"; dialog.showModal();
    requestAnimationFrame(focusStep);
    track("brand_review_opened", { package: selected.textContent });
  }));
  dialog.querySelectorAll("[data-dialog-close]").forEach(button => button.addEventListener("click", () => dialog.close()));
  dialog.addEventListener("click", event => { if (event.target === dialog) dialog.close(); });
  dialog.addEventListener("close", () => { delete document.body.dataset.brandDialogOpen; lastTrigger?.focus({ preventScroll: true }); });
  next.addEventListener("click", () => { if (valid()) { current++; validation.hidden = true; render(); focusStep(); track("brand_review_step", { step: current }); } });
  back.addEventListener("click", () => { if (current > 1 && !pending) { current--; validation.hidden = true; render(); focusStep(); } });
  form.addEventListener("input", event => { (event.target as HTMLElement).removeAttribute("aria-invalid"); });
  form.addEventListener("submit", async event => {
    event.preventDefault();
    if (pending) return;
    if (current < 3) { next.click(); return; }
    if (!valid()) return;
    const payload = new FormData(form), submittedPackage = selected.textContent;
    pending = true; error.hidden = true; render();
    try {
      const response = await fetch(form.action, { method: "POST", body: payload, headers: { Accept: "application/json" } });
      if (!response.ok) throw new Error("Review submission failed");
      const result = await response.json().catch(() => null) as { success?: boolean | string } | null;
      if (result?.success === false || result?.success === "false") throw new Error("Review submission failed");
      completed = true; form.reset(); form.hidden = true; progress.hidden = true; success.hidden = false;
      if (dialog.open) success.focus();
      track("brand_review_success", { package: submittedPackage });
    } catch {
      error.hidden = false;
      if (dialog.open) error.scrollIntoView({ block: "nearest" });
    } finally { pending = false; render(); }
  });
  render();
}

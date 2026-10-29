/* Provide visible, keyboard-accessible slide navigation alongside the deck's own shortcuts. */
(() => {
  function mount() {
    const deck = document.querySelector('.brand-story');
    if (!deck || deck.querySelector('.kw-deck-controls')) return;
    const fa = deck.lang === 'fa';
    const controls = document.createElement('div');
    controls.className = 'kw-deck-controls';
    for (const [key, label, path] of [
      ['PageUp', fa ? 'اسلاید قبلی' : 'Previous slide', fa ? 'M9 5l7 7-7 7' : 'M15 5l-7 7 7 7'],
      ['PageDown', fa ? 'اسلاید بعدی' : 'Next slide', fa ? 'M15 5l-7 7 7 7' : 'M9 5l7 7-7 7']
    ]) {
      const button = document.createElement('button');
      button.type = 'button';
      button.setAttribute('aria-label', label);
      button.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="${path}"/></svg>`;
      button.addEventListener('click', () => document.body.dispatchEvent(new KeyboardEvent('keydown', {key, bubbles: true})));
      controls.append(button);
    }
    const download = document.createElement('a');
    download.href = `/assets/presentations/downloads/brand-${fa ? 'fa' : 'en'}.pdf`;
    download.download = '';
    download.className = 'kw-deck-download';
    download.textContent = fa ? 'دانلود PDF' : 'Download PDF';
    controls.append(download);
    deck.append(controls);
  }
  new MutationObserver(mount).observe(document.body, {childList: true, subtree: true});
  mount();
})();

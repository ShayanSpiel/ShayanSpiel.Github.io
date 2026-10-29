import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

for (const [locale, path, expected] of [
  ['English', 'public/brand/index.html', ['5 social templates', '5 branded images', '5 branded assets', '5 branded short videos', 'Coded design system', '5 custom workflows']],
  ['Persian', 'public/fa/brand/index.html', ['۵ قالب شبکه‌های اجتماعی', '۵ تصویر برندشده', '۵ دارایی برندشده', '۵ ویدیوی کوتاه برندشده', 'دیزاین سیستم کدنویسی‌شده', '۵ ورک‌فلوی اختصاصی']]
]) {
  test(`${locale} brand packages and tool lockup`, () => {
    const html = readFileSync(path, 'utf8');
    for (const item of expected) assert.ok(html.includes(item), `Missing ${item}`);
    assert.match(html, /class="brand-tool-lockup" dir="ltr"/);
    assert.match(html, /assets\/brand\/figma\.svg/);
    assert.match(html, /assets\/brand\/chatgpt\.svg/);
    const cards = [...html.matchAll(/<article class="package-card[^>]*>[\s\S]*?<\/article>/g)].map(m => m[0]);
    assert.equal(cards.length, 3);
    for (const card of cards) assert.match(card, /href="\/(?:fa\/)?contact\/"/);
  });
}

test('localized presentation PDFs exist and presentation pages link to them', () => {
  for (const locale of ['en', 'fa']) {
    for (const [deck, route] of [['godae', 'godae'], ['transformation', 'ai-transformation']]) {
      const name = `${deck}-${locale}.pdf`;
      const pdf = readFileSync(`public/assets/presentations/downloads/${name}`);
      assert.equal(pdf.subarray(0, 5).toString(), '%PDF-');
      const html = readFileSync(`public/${locale}/presentations/${route}/index.html`, 'utf8');
      assert.ok(html.includes(`/assets/presentations/downloads/${name}`));
    }
    const pdf = readFileSync(`public/assets/presentations/downloads/brand-${locale}.pdf`);
    assert.equal(pdf.subarray(0, 5).toString(), '%PDF-');
  }
  assert.match(readFileSync('public/brand-guide-controls.js', 'utf8'), /brand-\$\{fa \? 'fa' : 'en'\}\.pdf/);
});

test('contact and chat use the current contact route', () => {
  for (const file of ['public/contact/index.html', 'public/fa/contact/index.html']) {
    assert.doesNotMatch(readFileSync(file, 'utf8'), /href="\/(?:fa\/)?apply\//);
  }
  const chat = readFileSync('public/assets/compiled/ChatAssistant.astro_astro_type_script_index_0_lang.D2PvvfJ9.js', 'utf8');
  assert.match(chat, /i\.href=u==="fa"\?"\/fa\/contact\/":"\/contact\/"/);
});

test('presentation controls are available in both brand-guide shells', () => {
  const controls = readFileSync('public/brand-guide-controls.js', 'utf8');
  assert.match(controls, /PageUp/);
  assert.match(controls, /PageDown/);
  for (const file of ['public/brand-guide/index.html', 'public/fa/brand-guide/index.html']) {
    const html = readFileSync(file, 'utf8');
    assert.match(html, /brand-guide-controls\.js/);
    assert.match(html, /presentation-polish\.css/);
  }
});

test('brand guide is accessible without collecting an email', () => {
  const deck = readFileSync('public/assets/compiled/BrandStoryDeck.C9meqHVP.js', 'utf8');
  assert.doesNotMatch(deck, /brand-story-email|spielos\.brand-guide-access|formAction/);
  assert.match(deck, /className:"brand-story-start",onClick:\(\)=>A\(1\)/);
  for (const file of ['public/brand-guide/index.html', 'public/fa/brand-guide/index.html']) {
    const html = readFileSync(file, 'utf8');
    assert.doesNotMatch(html, /brand-story-email|formsubmit\.co\/ajax|"formAction"/);
    assert.match(html, /class="brand-story-start"/);
  }
});

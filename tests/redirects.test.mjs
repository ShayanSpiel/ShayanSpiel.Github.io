import test from 'node:test';
import assert from 'node:assert/strict';
import {existsSync, readFileSync, readdirSync} from 'node:fs';
import {join} from 'node:path';
import {execFileSync} from 'node:child_process';

const routes = JSON.parse(readFileSync('scripts/retired-routes.json', 'utf8'));
test('retired pages resolve directly to existing current pages', () => {
  for (const [source, target] of Object.entries({ '/apply/': '/contact/', '/apply/thank-you/': '/contact/', '/fa/apply/': '/fa/contact/', '/fa/apply/thank-you/': '/fa/contact/' })) assert.equal(routes[source], target);
  for (const [source, target] of Object.entries(routes)) {
    assert.ok(existsSync(join('public', source, 'index.html')), `${source} source is preserved`);
    assert.ok(existsSync(join('public', target, 'index.html')), `${target} exists`);
    assert.equal(routes[target], undefined, `${source} has a redirect chain`);
  }
});
test('production snapshot preserves queries and excludes retired pages from sitemap', () => {
  if (!existsSync('dist/sitemap.xml')) execFileSync(process.execPath, ['scripts/build-karwise.mjs']);
  const sitemap = readFileSync('dist/sitemap.xml', 'utf8');
  for (const [source, target] of Object.entries(routes)) {
    const page = readFileSync(join('dist', source, 'index.html'), 'utf8');
    assert.ok(page.includes(`location.replace(${JSON.stringify(target)}+location.search+location.hash)`), source);
    assert.match(page, /noindex,follow/);
    assert.ok(!sitemap.includes(`<loc>https://spielos.xyz${source}</loc>`), source);
  }
});

test('active pages never link to the retired Apply funnel', () => {
  function walk(dir) {
    return readdirSync(dir, {withFileTypes: true}).flatMap(entry => entry.isDirectory() ? walk(join(dir, entry.name)) : [join(dir, entry.name)]);
  }
  for (const file of walk('dist').filter(path => path.endsWith('.html'))) {
    const html = readFileSync(file, 'utf8');
    if (/http-equiv=["']refresh/i.test(html)) continue;
    assert.doesNotMatch(html, /(?:href|action)=["'][^"']*\/(?:fa\/)?apply(?:\/|["'?#])/i, file);
  }
});

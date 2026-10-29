import test from 'node:test';
import assert from 'node:assert/strict';
import {existsSync, readFileSync} from 'node:fs';
import {join} from 'node:path';
import {execFileSync} from 'node:child_process';

const routes = JSON.parse(readFileSync('scripts/retired-routes.json', 'utf8'));
test('retired pages resolve directly to existing current pages', () => {
  assert.equal(Object.keys(routes).length, 158);
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

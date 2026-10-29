import {cpSync, existsSync, mkdirSync, readdirSync} from 'node:fs';
import {join} from 'node:path';
import {execFileSync} from 'node:child_process';

if (!existsSync('public/site-version.json')) throw Error('Missing reviewed snapshot');

// Keep existing files intact. Refuse a stale output instead of deleting it.
function assertNoStaleOutput(source, output) {
  if (!existsSync(output)) return;
  for (const entry of readdirSync(output, {withFileTypes: true})) {
    const src = join(source, entry.name);
    const dst = join(output, entry.name);
    if (!existsSync(src)) throw Error(`Stale build output requires review: ${dst}`);
    if (entry.isDirectory()) assertNoStaleOutput(src, dst);
  }
}
assertNoStaleOutput('public', 'dist');
mkdirSync('dist', {recursive: true});
cpSync('public', 'dist', {recursive: true});
execFileSync(process.execPath, ['scripts/build-redirects.mjs'], {stdio: 'inherit'});
console.log('Built Karwise public snapshot');

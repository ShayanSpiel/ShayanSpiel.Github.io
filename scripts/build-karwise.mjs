import {cpSync,existsSync,mkdirSync,rmSync} from 'node:fs';
if(!existsSync('public/site-version.json'))throw Error('Missing reviewed snapshot');
if(existsSync('dist'))rmSync('dist',{recursive:true});mkdirSync('dist');cpSync('public','dist',{recursive:true});
console.log('Built Karwise public snapshot');

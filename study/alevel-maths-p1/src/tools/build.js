// Usage: node build.js in.md out.html
const fs = require('fs');
const path = require('path');
const katex = require('katex');
const md = require('markdown-it')({ html: true, breaks: process.env.MD_BREAKS === '1' });
const [,, inFile, outFile] = process.argv;
let src = fs.readFileSync(inFile, 'utf8');
const holds = [];
function hold(html){ holds.push(html); return `QQMATH${holds.length-1}QQ`; }
// display math $$...$$
src = src.replace(/\$\$([\s\S]+?)\$\$/g, (m, tex) => hold(katex.renderToString(tex, {displayMode:true, throwOnError:false})));
// inline math $...$ (no newlines)
src = src.replace(/\$([^\$\n]+?)\$/g, (m, tex) => hold(katex.renderToString(tex, {displayMode:false, throwOnError:false})));
let html = md.render(src);
html = html.replace(/QQMATH(\d+)QQ/g, (m, i) => holds[+i]);
const cssPath = path.resolve(__dirname, 'node_modules/katex/dist/katex.min.css');
const page = `<!doctype html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="file://${cssPath}">
<style>
@page { size: A4; margin: 18mm 16mm 18mm 16mm; }
body { font-family: "Times New Roman", "Liberation Serif", serif; font-size: 11.5pt; line-height: 1.45; color:#000; }
h1 { font-size: 15pt; margin: 0 0 4pt 0; }
h2 { font-size: 12.5pt; margin: 14pt 0 4pt 0; border-bottom: 1px solid #999; }
h3 { font-size: 11.5pt; margin: 10pt 0 2pt 0; }
table { border-collapse: collapse; margin: 6pt 0; }
td, th { border: 1px solid #666; padding: 3pt 7pt; font-size: 10.5pt; vertical-align: top; }
.q { margin: 12pt 0 0 0; page-break-inside: avoid; }
.marks { float: right; font-weight: normal; }
.box { border: 1px solid #000; padding: 6pt 10pt; margin: 8pt 0; font-size: 10.5pt; }
.pb { page-break-before: always; }
.small { font-size: 10pt; color:#333; }
hr { border: 0; border-top: 1px solid #999; margin: 10pt 0; }
ol.parts { padding-left: 22pt; }
ol.parts li { margin: 3pt 0; }
svg.fig { display:block; margin: 6pt auto; }
.katex { font-size: 1.02em; }
blockquote { margin: 4pt 0 4pt 14pt; padding-left: 8pt; border-left: 2px solid #aaa; color:#222; }
</style></head><body>${html}</body></html>`;
fs.writeFileSync(outFile, page);

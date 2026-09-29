// usage: node render.js <outdir> <mode front|depth|mask> <scale 1|2> frames <from> <to> [workers]
//        node render.js <outdir> <mode> <scale> times t1,t2,...
// Frame i is output time i/60. Camera-shake offsets come from ../shake.json (same values comp.py uses).
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const FPS = 60;

async function worker(browser, scale, mode, frames, outdir, shake) {
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: scale });
  await page.goto('file://' + path.resolve(__dirname, 'overlay.html'));
  await page.evaluate(() => document.fonts.ready);
  await page.evaluate(() => window.setup());
  for (const [name, t] of frames) {
    const k = Math.round(t * FPS);
    await page.evaluate(([t, m, s]) => window.render(t, m, s), [t, mode, shake[k] || [0, 0]]);
    await page.screenshot({ path: path.join(outdir, name), omitBackground: true, type: 'png' });
  }
  await page.close();
}

(async () => {
  const [outdir, mode, scaleS, kind, a, b, w] = process.argv.slice(2);
  const scale = parseFloat(scaleS);
  fs.mkdirSync(outdir, { recursive: true });
  const shake = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'shake.json')));
  let frames = [], workers = 1;
  if (kind === 'times') frames = a.split(',').map((t) => [`t_${t}.png`, parseFloat(t)]);
  else {
    for (let i = parseInt(a); i <= parseInt(b); i++) frames.push([`f_${String(i).padStart(5, '0')}.png`, i / FPS]);
    workers = parseInt(w || '3');
  }
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
  const parts = Array.from({ length: workers }, (_, k) => frames.filter((_, i) => i % workers === k));
  await Promise.all(parts.map((p) => worker(browser, scale, mode, p, outdir, shake)));
  await browser.close();
})();

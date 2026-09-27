// usage: node render.js <outdir> <fps> <dur> [workers]  |  node render.js <outdir> times t1,t2,...
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

async function worker(browser, caps, frames, outdir) {
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 2 });
  await page.goto('file://' + path.resolve(__dirname, 'overlay.html'));
  await page.evaluate((c) => window.setup(c), caps);
  await page.evaluate(() => document.fonts.ready);
  for (const [name, t] of frames) {
    await page.evaluate((t) => window.render(t), t);
    await page.screenshot({ path: path.join(outdir, name), omitBackground: true, type: 'png' });
  }
  await page.close();
}

(async () => {
  const [outdir, mode, a, b] = process.argv.slice(2);
  fs.mkdirSync(outdir, { recursive: true });
  const caps = JSON.parse(fs.readFileSync(path.join(__dirname, 'captions.json')));
  let frames = [];
  let workers = 1;
  if (mode === 'times') {
    frames = a.split(',').map((t) => [`t_${t}.png`, parseFloat(t)]);
  } else {
    const fps = parseFloat(mode), dur = parseFloat(a);
    workers = parseInt(b || '3');
    const n = Math.ceil(dur * fps);
    for (let i = 0; i < n; i++) frames.push([`f_${String(i).padStart(5, '0')}.png`, i / fps]);
  }
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
  const parts = Array.from({ length: workers }, (_, w) => frames.filter((_, i) => i % workers === w));
  await Promise.all(parts.map((p) => worker(browser, caps, p, outdir)));
  await browser.close();
})();

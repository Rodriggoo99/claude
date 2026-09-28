// usage:
//   node render.js <outdir> frames <fps> <n_frames> [workers] [dsf]   -> f_XXXXX.png (front) + b_XXXXX.png (depth layer, only when present)
//   node render.js <outdir> times t1,t2,...  [dsf]                    -> t_<t>.png (front) + tb_<t>.png (depth layer), for checks
//   node render.js <outdir> measure <fps> <n_frames> [workers]         -> m_XXXXX.png (content only, screen paper hidden) for safe-margin checks
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

async function worker(browser, caps, frames, outdir, dsf, mode) {
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: dsf });
  await page.goto('file://' + path.resolve(__dirname, 'overlay.html'));
  await page.evaluate(async () => {
    await Promise.all(['600 20px Inter', '700 20px Inter', '800 20px InterTight', '900 20px InterTight', 'italic 20px Serif', '20px Serif'].map((f) => document.fonts.load(f)));
    await document.fonts.ready;
  });
  await page.evaluate((c) => window.setup(c), caps);
  if (mode === 'measure') await page.evaluate(() => document.body.classList.add('measure'));
  for (const [name, t] of frames) {
    await page.evaluate((layer) => { document.body.dataset.layer = layer; }, mode === 'measure' ? 'all' : 'front');
    const back = await page.evaluate((t) => window.render(t), t);
    await page.screenshot({ path: path.join(outdir, name), omitBackground: true, type: 'png' });
    if (mode !== 'measure' && back) {
      await page.evaluate(() => { document.body.dataset.layer = 'back'; });
      await page.screenshot({ path: path.join(outdir, name.replace(/^f_/, 'b_').replace(/^t_/, 'tb_')), omitBackground: true, type: 'png' });
    }
  }
  await page.close();
}

(async () => {
  const [outdir, mode, a, b, c, d] = process.argv.slice(2);
  fs.mkdirSync(outdir, { recursive: true });
  const caps = JSON.parse(fs.readFileSync(path.join(__dirname, 'captions.json')));
  let frames = [], workers = 1, dsf = 1;
  if (mode === 'times') {
    frames = a.split(',').map((t) => [`t_${t}.png`, parseFloat(t)]);
    dsf = parseFloat(b || '0.5');
  } else {
    const fps = parseFloat(a), n = parseInt(b);
    workers = parseInt(c || '3');
    dsf = mode === 'measure' ? 0.5 : parseFloat(d || '1');
    const lo = parseInt(process.env.FROM || '0'), hi = Number(process.env.TO || 1e9);
    const pre = mode === 'measure' ? 'm_' : 'f_';
    for (let i = 0; i < n; i++) if (i >= lo && i <= hi) frames.push([`${pre}${String(i).padStart(5, '0')}.png`, i / fps]);
  }
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
  const parts = Array.from({ length: workers }, (_, w) => frames.filter((_, i) => i % workers === w));
  await Promise.all(parts.map((p) => worker(browser, caps, p, outdir, dsf, mode)));
  await browser.close();
})();

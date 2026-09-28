// usage: [DSF=1|2] node render.js <outdir> <fps> <dur> [workers]   -> <outdir>/front/f_#####.png + <outdir>/back/f_#####.png (only when used)
//        [DSF=1|2] node render.js <outdir> times t1,t2,...
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const DSF = parseFloat(process.env.DSF || '2');

async function worker(browser, caps, frames, outdir) {
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: DSF });
  await page.goto('file://' + path.resolve(__dirname, 'overlay.html'));
  await page.evaluate((c) => window.setup(c), caps);
  await page.evaluate(() => document.fonts.ready);
  for (const [name, t] of frames) {
    for (const layer of ['back', 'front']) {
      const used = await page.evaluate(([t, l]) => window.render(t, l), [t, layer]);
      if (used) await page.screenshot({ path: path.join(outdir, layer, name), omitBackground: true, type: 'png' });
    }
  }
  await page.close();
}

(async () => {
  const [outdir, mode, a, b] = process.argv.slice(2);
  for (const l of ['front', 'back']) fs.mkdirSync(path.join(outdir, l), { recursive: true });
  const caps = JSON.parse(fs.readFileSync(path.join(__dirname, 'captions.json')));
  let frames = [];
  let workers = 1;
  if (mode === 'times') {
    frames = a.split(',').map((t) => [`t_${t}.png`, parseFloat(t)]);
  } else {
    const fps = parseFloat(mode), dur = parseFloat(a);
    workers = parseInt(b || '3');
    const n = Math.ceil(dur * fps);
    const lo = parseInt(process.env.FROM || '0'), hi = Number(process.env.TO || 1e9);
    for (let i = 0; i < n; i++) if (i >= lo && i <= hi) frames.push([`f_${String(i).padStart(5, '0')}.png`, i / fps]);
  }
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
  const parts = Array.from({ length: workers }, (_, w) => frames.filter((_, i) => i % workers === w));
  await Promise.all(parts.map((p) => worker(browser, caps, p, outdir)));
  await browser.close();
})();

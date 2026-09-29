const { chromium } = require('playwright'); const path = require('path');
(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
  const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  for (const [name, y, cls, acc] of [['A', 1440 - 70 - 20, 'ink', '#15120E'], ['B', 470, 'white', '#F2B24C'], ['C', 470, 'ink', '#15120E']]) {
    await p.goto('file://' + path.resolve(__dirname, 'test.html') + `?y=${y}&cls=${cls}&acc=${encodeURIComponent(acc)}`);
    await p.evaluate(() => document.fonts.ready);
    await p.screenshot({ path: `/home/user/work/cd/test/ov_${name}.png`, omitBackground: true });
  }
  await b.close();
})();

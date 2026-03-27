import { test } from '@playwright/test';

test('inspect halowebui dev page', async ({ page }) => {
  const logs = [];

  page.on('console', (msg) => logs.push(`[console:${msg.type()}] ${msg.text()}`));
  page.on('pageerror', (err) => logs.push(`[pageerror] ${err.message}`));
  page.on('response', (res) => {
    if (res.status() >= 400) logs.push(`[response ${res.status()}] ${res.url()}`);
  });

  await page.goto('http://127.0.0.1:5173', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(5000);

  const data = await page.evaluate(() => ({
    url: location.href,
    title: document.title,
    text: document.body.innerText.slice(0, 1000),
    htmlSnippet: document.body.innerHTML.slice(0, 1500),
    localStorageKeys: Object.keys(localStorage),
  }));

  console.log('PW_RESULT_START');
  console.log(JSON.stringify({ data, logs }, null, 2));
  console.log('PW_RESULT_END');
});

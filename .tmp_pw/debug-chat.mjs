import { chromium } from 'playwright';

const CHAT_ID = '0b79b696-cae6-459a-94fb-591ad9acaa1a';

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({
  storageState: './storage_state.json',
  viewport: { width: 1440, height: 1000 }
});
const page = await context.newPage();

const logs = [];
page.on('console', (msg) => {
  if (['error', 'warning'].includes(msg.type())) logs.push(`[console:${msg.type()}] ${msg.text()}`);
});
page.on('pageerror', (err) => logs.push(`[pageerror] ${err.message}`));

await page.goto(`http://127.0.0.1:5173/c/${CHAT_ID}`, { waitUntil: 'domcontentloaded', timeout: 30000 });
await page.waitForTimeout(8000);

await page.locator('button').nth(12).click();
await page.waitForTimeout(1200);
await page.getByText('Overview', { exact: true }).click();
await page.waitForTimeout(2500);
await page.screenshot({ path: '/tmp/overview-open.png', fullPage: true });

const paneMetrics = await page.evaluate(() => {
  const panes = Array.from(document.querySelectorAll('[data-pane]'));
  const resizers = Array.from(document.querySelectorAll('[data-pane-resizer]'));
  const overviewTitle = Array.from(document.querySelectorAll('div'))
    .find((el) => el.textContent?.trim() === '对话概述' || el.textContent?.trim() === 'Chat Overview');

  return {
    viewport: {
      width: window.innerWidth,
      height: window.innerHeight
    },
    panes: panes.map((el, index) => {
      const rect = el.getBoundingClientRect();
      return {
        index,
        x: Math.round(rect.x),
        y: Math.round(rect.y),
        width: Math.round(rect.width),
        height: Math.round(rect.height),
        style: el.getAttribute('style'),
        className: el.className
      };
    }),
    resizers: resizers.map((el, index) => {
      const rect = el.getBoundingClientRect();
      return {
        index,
        x: Math.round(rect.x),
        y: Math.round(rect.y),
        width: Math.round(rect.width),
        height: Math.round(rect.height),
        className: el.className
      };
    }),
    overviewTitleRect: overviewTitle
      ? (() => {
          const rect = overviewTitle.getBoundingClientRect();
          return {
            x: Math.round(rect.x),
            y: Math.round(rect.y),
            width: Math.round(rect.width),
            height: Math.round(rect.height)
          };
        })()
      : null
  };
});

console.log(JSON.stringify({ logs, paneMetrics }, null, 2));

await browser.close();

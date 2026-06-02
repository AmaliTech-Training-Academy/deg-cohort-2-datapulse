import { chromium } from '@playwright/test';

export default async function globalSetup() {
  const browser = await chromium.launch();
  const page = await browser.newPage();

  // Pre-warm all lazy-loaded route chunks so Angular compilation
  // finishes before the parallel test workers start navigating.
  await page.goto('http://localhost:4200/login', { timeout: 120_000 });
  await page.goto('http://localhost:4200/register', { timeout: 60_000 });
  await page.goto('http://localhost:4200/reset-password', { timeout: 60_000 });

  await browser.close();
}

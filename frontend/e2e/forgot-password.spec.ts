import { test, expect } from '@playwright/test';

const API_FORGOT_PASSWORD = '**/v1/auth/forgot-password/';

test.describe('Forgot Password page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/forgot-password');
  });

  test('renders the email field and submit button', async ({ page }) => {
    await expect(page.getByLabel(/email/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /send reset link/i })).toBeVisible();
  });

  test('has a back to sign in link', async ({ page }) => {
    await expect(page.getByRole('link', { name: /back to sign in/i })).toBeVisible();
  });

  test('does not show the success card initially', async ({ page }) => {
    await expect(page.getByText(/check your email/i)).not.toBeVisible();
  });

  test('shows required validation error on empty submit', async ({ page }) => {
    await page.getByRole('button', { name: /send reset link/i }).click();
    await expect(page.getByRole('alert')).toBeVisible();
  });

  test('shows email validation error for an invalid email', async ({ page }) => {
    await page.getByLabel(/email/i).fill('not-valid');
    await page.getByRole('button', { name: /send reset link/i }).click();
    await expect(page.getByText(/enter a valid email/i)).toBeVisible();
  });

  test('shows success card and hides form after successful submission', async ({ page }) => {
    await page.route(API_FORGOT_PASSWORD, (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({}),
      }),
    );

    await page.getByLabel(/email/i).fill('user@example.com');
    await page.getByRole('button', { name: /send reset link/i }).click();

    await expect(page.getByText(/check your email/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /send reset link/i })).not.toBeVisible();
  });

  test('navigates to /login via the back to sign in link', async ({ page }) => {
    await page.getByRole('link', { name: /back to sign in/i }).click();
    await page.waitForURL('**/login');
    expect(page.url()).toContain('/login');
  });
});

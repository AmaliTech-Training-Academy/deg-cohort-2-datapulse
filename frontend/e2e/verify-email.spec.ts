import { test, expect } from '@playwright/test';

const API_VERIFY_EMAIL = '**/v1/auth/verify-email/';

test.describe('Verify Email page', () => {
  test('shows error state when no token in URL', async ({ page }) => {
    await page.goto('/verify-email');
    await expect(page.getByRole('alert')).toBeVisible();
    await expect(page.getByText(/no verification token/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /resend verification email/i })).toBeVisible();
  });

  test.describe('with token in URL', () => {
    test('shows success state after valid token verification', async ({ page }) => {
      await page.route(API_VERIFY_EMAIL, (route) =>
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({}),
        }),
      );

      await page.goto('/verify-email?token=valid-token-abc');

      await expect(page.getByText(/email verified!/i)).toBeVisible();
      await expect(page.getByRole('link', { name: /go to sign in/i })).toBeVisible();
    });

    test('shows error and resend form on invalid/expired token (400)', async ({ page }) => {
      await page.route(API_VERIFY_EMAIL, (route) =>
        route.fulfill({
          status: 400,
          contentType: 'application/json',
          body: JSON.stringify({ detail: 'Token is invalid or expired' }),
        }),
      );

      await page.goto('/verify-email?token=expired-token');

      await expect(page.getByRole('alert')).toBeVisible();
      await expect(page.getByRole('button', { name: /resend verification email/i })).toBeVisible();
    });
  });
});

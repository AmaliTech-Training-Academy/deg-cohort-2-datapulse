import { test, expect } from '@playwright/test';

const API_RESET_PASSWORD = '**/v1/auth/reset-password/';

test.describe('Reset Password page (token-based)', () => {
  test('shows invalid link error when uid or token are missing', async ({ page }) => {
    await page.goto('/reset-password');
    await expect(page.getByText(/invalid reset link/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /set new password/i })).not.toBeVisible();
  });

  test.describe('with valid uid and token in URL', () => {
    test.beforeEach(async ({ page }) => {
      await page.goto('/reset-password?uid=test-uid&token=test-token');
    });

    test('renders password and confirm password fields', async ({ page }) => {
      await expect(page.locator('input[type="password"]').first()).toBeVisible();
      await expect(page.getByRole('button', { name: /set new password/i })).toBeVisible();
    });

    test('has a back to sign in link', async ({ page }) => {
      await expect(page.getByRole('link', { name: /back to sign in/i })).toBeVisible();
    });

    test('shows success card after successful password reset', async ({ page }) => {
      await page.route(API_RESET_PASSWORD, (route) =>
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({}),
        }),
      );

      const passwordInputs = page.locator('input[type="password"]');
      await passwordInputs.nth(0).fill('newpassword123');
      await passwordInputs.nth(1).fill('newpassword123');
      await page.getByRole('button', { name: /set new password/i }).click();

      await expect(page.getByText(/password reset!/i)).toBeVisible();
      await expect(page.getByRole('link', { name: /back to sign in/i })).toBeVisible();
    });

    test('shows error alert on invalid/expired token (400)', async ({ page }) => {
      await page.route(API_RESET_PASSWORD, (route) =>
        route.fulfill({
          status: 400,
          contentType: 'application/json',
          body: JSON.stringify({ detail: 'Token is invalid or expired' }),
        }),
      );

      const passwordInputs = page.locator('input[type="password"]');
      await passwordInputs.nth(0).fill('newpassword123');
      await passwordInputs.nth(1).fill('newpassword123');
      await page.getByRole('button', { name: /set new password/i }).click();

      await expect(page.getByRole('alert')).toBeVisible();
      expect(page.url()).toContain('/reset-password');
    });
  });
});

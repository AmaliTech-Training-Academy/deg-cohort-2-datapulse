import { test, expect } from '@playwright/test';

const API_LOGIN = '**/v1/auth/login/';

const mockUser = {
  id: '1',
  email: 'user@example.com',
  first_name: 'Test',
  last_name: 'User',
  role: 'user',
  created_at: '2026-06-03T00:00:00Z',
  is_email_verified: true,
};

test.describe('Login page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
  });

  test('renders the email and password fields and submit button', async ({ page }) => {
    await expect(page.getByLabel(/email/i)).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
    await expect(page.getByRole('button', { name: /sign in/i })).toBeVisible();
  });

  test('shows a forgot password link and create an account link', async ({ page }) => {
    await expect(page.getByRole('link', { name: /forgot password/i })).toBeVisible();
    await expect(page.getByRole('link', { name: /create an account/i })).toBeVisible();
  });

  test('shows required validation errors on empty submit', async ({ page }) => {
    await page.getByRole('button', { name: /sign in/i }).click();
    await expect(page.getByRole('alert').first()).toBeVisible();
  });

  test('shows email validation error for an invalid email', async ({ page }) => {
    await page.getByLabel(/email/i).fill('not-an-email');
    await page.locator('input[type="password"]').fill('password123');
    await page.getByRole('button', { name: /sign in/i }).click();
    await expect(page.getByText(/enter a valid email/i)).toBeVisible();
  });

  test('shows error alert on invalid credentials (401)', async ({ page }) => {
    await page.route(API_LOGIN, (route) =>
      route.fulfill({
        status: 400,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Invalid credentials' }),
      }),
    );

    await page.getByLabel(/email/i).fill('wrong@example.com');
    await page.locator('input[type="password"]').fill('wrongpassword');
    await page.getByRole('button', { name: /sign in/i }).click();

    await expect(page.getByRole('alert')).toBeVisible();
    await expect(page.url()).toContain('/login');
  });

  test('shows resend verification button on email-not-verified error', async ({ page }) => {
    await page.route(API_LOGIN, (route) =>
      route.fulfill({
        status: 400,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Email not verified' }),
      }),
    );

    await page.getByLabel(/email/i).fill('unverified@example.com');
    await page.locator('input[type="password"]').fill('password123');
    await page.getByRole('button', { name: /sign in/i }).click();

    await expect(page.getByRole('button', { name: /resend verification/i })).toBeVisible();
  });

  test('navigates to /dashboard on successful login', async ({ page }) => {
    await page.route(API_LOGIN, (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ access: 'acc-tok', refresh: 'ref-tok', user: mockUser }),
      }),
    );

    await page.getByLabel(/email/i).fill('user@example.com');
    await page.locator('input[type="password"]').fill('correctpassword');
    await page.getByRole('button', { name: /sign in/i }).click();

    await page.waitForURL('**/dashboard/**');
    expect(page.url()).toContain('/dashboard');
  });

  test('navigates to /forgot-password via the forgot password link', async ({ page }) => {
    await page.getByRole('link', { name: /forgot password/i }).click();
    await page.waitForURL('**/forgot-password');
    expect(page.url()).toContain('/forgot-password');
  });

  test('navigates to /register via the create an account link', async ({ page }) => {
    await page.getByRole('link', { name: /create an account/i }).click();
    await page.waitForURL('**/register');
    expect(page.url()).toContain('/register');
  });
});

import { test, expect } from '@playwright/test';

const API_REGISTER = '**/v1/auth/register/';

const mockUser = {
  id: '2',
  email: 'newuser@example.com',
  first_name: 'New',
  last_name: 'User',
  role: 'user',
  created_at: '2026-06-03T00:00:00Z',
  is_email_verified: false,
};

test.describe('Register page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/register');
  });

  test('renders all form fields and the submit button', async ({ page }) => {
    await expect(page.getByLabel(/first name/i)).toBeVisible();
    await expect(page.getByLabel(/last name/i)).toBeVisible();
    await expect(page.getByLabel(/email/i)).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
    await expect(page.getByRole('button', { name: /create account/i })).toBeVisible();
  });

  test('has a sign in link', async ({ page }) => {
    await expect(page.getByRole('link', { name: /sign in/i })).toBeVisible();
  });

  test('shows required validation errors on empty submit', async ({ page }) => {
    await page.getByRole('button', { name: /create account/i }).click();
    await expect(page.getByRole('alert').first()).toBeVisible();
  });

  test('shows password minlength error for short password', async ({ page }) => {
    await page.getByLabel(/first name/i).fill('Jordan');
    await page.getByLabel(/last name/i).fill('Lee');
    await page.getByLabel(/email/i).fill('jordan@example.com');
    await page.locator('input[type="password"]').fill('short');
    await page.getByRole('button', { name: /create account/i }).click();
    await expect(page.getByText(/minimum 8 characters/i)).toBeVisible();
  });

  test('shows error alert on duplicate email (400)', async ({ page }) => {
    await page.route(API_REGISTER, (route) =>
      route.fulfill({
        status: 400,
        contentType: 'application/json',
        body: JSON.stringify({ email: ['A user with this email already exists.'] }),
      }),
    );

    await page.getByLabel(/first name/i).fill('Jordan');
    await page.getByLabel(/last name/i).fill('Lee');
    await page.getByLabel(/email/i).fill('existing@example.com');
    await page.locator('input[type="password"]').fill('password123');
    await page.getByRole('button', { name: /create account/i }).click();

    await expect(page.getByRole('alert')).toBeVisible();
    await expect(page.url()).toContain('/register');
  });

  test('shows check-your-inbox success card after successful registration', async ({ page }) => {
    await page.route(API_REGISTER, (route) =>
      route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify(mockUser),
      }),
    );

    await page.getByLabel(/first name/i).fill('New');
    await page.getByLabel(/last name/i).fill('User');
    await page.getByLabel(/email/i).fill('newuser@example.com');
    await page.locator('input[type="password"]').fill('securepassword');
    await page.getByRole('button', { name: /create account/i }).click();

    await expect(page.getByText(/check your inbox/i)).toBeVisible();
    expect(page.url()).toContain('/register');
  });

  test('navigates to /login via the sign in link', async ({ page }) => {
    await page.getByRole('link', { name: /sign in/i }).click();
    await page.waitForURL('**/login');
    expect(page.url()).toContain('/login');
  });
});

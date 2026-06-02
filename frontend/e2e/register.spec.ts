import { test, expect } from '@playwright/test';

const API_REGISTER = '**/auth/register';

const mockUser = { id: '2', email: 'newuser@example.com', name: 'New User' };

test.describe('Register page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/register');
  });

  test('renders all form fields and the submit button', async ({ page }) => {
    await expect(page.getByLabel(/first name/i)).toBeVisible();
    await expect(page.getByLabel(/last name/i)).toBeVisible();
    await expect(page.getByLabel(/email/i)).toBeVisible();
    await expect(page.getByLabel(/password/i)).toBeVisible();
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
    await page.getByLabel(/password/i).fill('short');
    await page.getByRole('button', { name: /create account/i }).click();
    await expect(page.getByText(/minimum 8 characters/i)).toBeVisible();
  });

  test('shows error alert on duplicate email (409)', async ({ page }) => {
    await page.route(API_REGISTER, (route) =>
      route.fulfill({
        status: 409,
        contentType: 'application/json',
        body: JSON.stringify({ message: 'Email already registered' }),
      }),
    );

    await page.getByLabel(/first name/i).fill('Jordan');
    await page.getByLabel(/last name/i).fill('Lee');
    await page.getByLabel(/email/i).fill('existing@example.com');
    await page.getByLabel(/password/i).fill('password123');
    await page.getByRole('button', { name: /create account/i }).click();

    await expect(page.getByRole('alert')).toBeVisible();
    await expect(page.url()).toContain('/register');
  });

  test('navigates to /dashboard on successful registration', async ({ page }) => {
    await page.route(API_REGISTER, (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ user: mockUser, token: 'new-user-token' }),
      }),
    );

    await page.getByLabel(/first name/i).fill('New');
    await page.getByLabel(/last name/i).fill('User');
    await page.getByLabel(/email/i).fill('newuser@example.com');
    await page.getByLabel(/password/i).fill('securepassword');
    await page.getByRole('button', { name: /create account/i }).click();

    await page.waitForURL('**/dashboard');
    expect(page.url()).toContain('/dashboard');
  });

  test('navigates to /login via the sign in link', async ({ page }) => {
    await page.getByRole('link', { name: /sign in/i }).click();
    await page.waitForURL('**/login');
    expect(page.url()).toContain('/login');
  });
});

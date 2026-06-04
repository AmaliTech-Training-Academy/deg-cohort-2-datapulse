import { render, screen, fireEvent } from '@testing-library/angular';
import { ForgotPasswordComponent } from './forgot-password';
import { provideMockStore, MockStore } from '@ngrx/store/testing';
import { provideRouter } from '@angular/router';
import { TestBed } from '@angular/core/testing';
import * as AuthActions from '../store/auth.actions';

const defaultAuthState = {
  user: null,
  loading: false,
  error: null,
  forgotPasswordSent: false,
  registrationComplete: false,
  emailVerificationSent: false,
  emailVerified: false,
  passwordResetSuccess: false,
};

describe('ForgotPasswordComponent', () => {
  async function setup(authState: Partial<typeof defaultAuthState> = {}) {
    await render(ForgotPasswordComponent, {
      providers: [
        provideMockStore({ initialState: { auth: { ...defaultAuthState, ...authState } } }),
        provideRouter([]),
      ],
    });
    return { store: TestBed.inject(MockStore) };
  }

  it('renders the email field', async () => {
    await setup();
    expect(screen.getByLabelText(/email/i)).toBeTruthy();
  });

  it('renders Send reset link button', async () => {
    await setup();
    expect(screen.getByRole('button', { name: /send reset link/i })).toBeTruthy();
  });

  it('has a back to sign in link', async () => {
    await setup();
    expect(screen.getByRole('link', { name: /back to sign in/i })).toBeTruthy();
  });

  it('shows error alert when store has error', async () => {
    await setup({ error: 'No account found with that email' });
    const alert = screen.getByRole('alert');
    expect(alert).toBeTruthy();
    expect(alert.textContent).toContain('No account found with that email');
  });

  it('disables the submit button when loading', async () => {
    await setup({ loading: true });
    expect(screen.getByRole('button', { name: /send reset link/i })).toBeDisabled();
  });

  it('dispatches forgotPassword action on valid submit', async () => {
    const { store } = await setup();
    const dispatchSpy = jest.spyOn(store, 'dispatch');

    fireEvent.input(screen.getByLabelText(/email/i), { target: { value: 'user@example.com' } });
    fireEvent.click(screen.getByRole('button', { name: /send reset link/i }));

    expect(dispatchSpy).toHaveBeenCalledWith(
      AuthActions.forgotPassword({ email: 'user@example.com' }),
    );
  });

  it('does not dispatch when email is empty', async () => {
    const { store } = await setup();
    const dispatchSpy = jest.spyOn(store, 'dispatch');
    fireEvent.click(screen.getByRole('button', { name: /send reset link/i }));
    expect(dispatchSpy).not.toHaveBeenCalled();
  });

  it('does not dispatch when email is invalid', async () => {
    const { store } = await setup();
    const dispatchSpy = jest.spyOn(store, 'dispatch');
    fireEvent.input(screen.getByLabelText(/email/i), { target: { value: 'not-an-email' } });
    fireEvent.click(screen.getByRole('button', { name: /send reset link/i }));
    expect(dispatchSpy).not.toHaveBeenCalled();
  });

  it('shows success card and hides form when forgotPasswordSent is true', async () => {
    await setup({ forgotPasswordSent: true });
    expect(screen.queryByRole('button', { name: /send reset link/i })).toBeNull();
    expect(screen.getByText(/check your email/i)).toBeTruthy();
  });
});

import { render, screen, fireEvent } from '@testing-library/angular';
import { ResetPasswordComponent } from './reset-password';
import { provideMockStore, MockStore } from '@ngrx/store/testing';
import { provideRouter, ActivatedRoute } from '@angular/router';
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

function makeActivatedRoute(params: Record<string, string> = {}) {
  return {
    snapshot: {
      queryParamMap: {
        get: (key: string) => params[key] ?? null,
      },
    },
  };
}

describe('ResetPasswordComponent', () => {
  async function setup(
    authState: Partial<typeof defaultAuthState> = {},
    queryParams: Record<string, string> = { uid: 'test-uid', token: 'test-token' },
  ) {
    await render(ResetPasswordComponent, {
      providers: [
        provideMockStore({ initialState: { auth: { ...defaultAuthState, ...authState } } }),
        provideRouter([]),
        { provide: ActivatedRoute, useValue: makeActivatedRoute(queryParams) },
      ],
    });
    return { store: TestBed.inject(MockStore) };
  }

  it('renders the password field when uid and token are present', async () => {
    await setup();
    expect(screen.getByLabelText(/new password/i, { selector: 'input' })).toBeTruthy();
  });

  it('renders Set new password button', async () => {
    await setup();
    expect(screen.getByRole('button', { name: /set new password/i })).toBeTruthy();
  });

  it('shows invalid link error when uid or token are missing', async () => {
    await setup({}, {});
    expect(screen.getByText(/invalid reset link/i)).toBeTruthy();
    expect(screen.queryByRole('button', { name: /set new password/i })).toBeNull();
  });

  it('shows error alert from store', async () => {
    await setup({ error: 'Token expired' });
    const alert = screen.getByRole('alert');
    expect(alert).toBeTruthy();
    expect(alert.textContent).toContain('Token expired');
  });

  it('disables the submit button when loading', async () => {
    await setup({ loading: true });
    expect(screen.getByRole('button', { name: /set new password/i })).toBeDisabled();
  });

  it('dispatches resetPassword with uid, token, and password on valid submit', async () => {
    const { store } = await setup();
    const dispatchSpy = jest.spyOn(store, 'dispatch');

    fireEvent.input(screen.getByLabelText(/new password/i, { selector: 'input' }), {
      target: { value: 'newpassword1' },
    });
    fireEvent.input(screen.getByLabelText(/confirm password/i, { selector: 'input' }), {
      target: { value: 'newpassword1' },
    });
    fireEvent.click(screen.getByRole('button', { name: /set new password/i }));

    expect(dispatchSpy).toHaveBeenCalledWith(
      AuthActions.resetPassword({ uid: 'test-uid', token: 'test-token', password: 'newpassword1' }),
    );
  });

  it('shows success card when passwordResetSuccess is true', async () => {
    await setup({ passwordResetSuccess: true });
    expect(screen.queryByRole('button', { name: /set new password/i })).toBeNull();
    expect(screen.getByText(/password reset!/i)).toBeTruthy();
  });
});

import { render, screen } from '@testing-library/angular';
import { VerifyEmailComponent } from './verify-email';
import { MockStore, provideMockStore } from '@ngrx/store/testing';
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

async function setup(
  authState: Partial<typeof defaultAuthState> = {},
  queryParams: Record<string, string> = { token: 'valid-token' },
) {
  await render(VerifyEmailComponent, {
    providers: [
      provideMockStore({ initialState: { auth: { ...defaultAuthState, ...authState } } }),
      provideRouter([]),
      { provide: ActivatedRoute, useValue: makeActivatedRoute(queryParams) },
    ],
  });
  return { store: TestBed.inject(MockStore) };
}

describe('VerifyEmailComponent', () => {
  afterEach(() => jest.restoreAllMocks());

  it('dispatches verifyEmail with token from route on init', async () => {
    // Spy before render so we capture the ngOnInit dispatch
    const dispatchSpy = jest.spyOn(MockStore.prototype, 'dispatch');
    await setup({}, { token: 'valid-token' });
    expect(dispatchSpy).toHaveBeenCalledWith(AuthActions.verifyEmail({ token: 'valid-token' }));
  });

  it('does not dispatch verifyEmail when no token in URL', async () => {
    const dispatchSpy = jest.spyOn(MockStore.prototype, 'dispatch');
    await setup({}, {});
    const verifyEmailCalls = dispatchSpy.mock.calls.filter(
      (call) => (call[0] as any).type === '[Auth] Verify Email',
    );
    expect(verifyEmailCalls).toHaveLength(0);
  });

  it('shows success state when emailVerified is true', async () => {
    await setup({ emailVerified: true });
    expect(screen.getByText(/email verified!/i)).toBeTruthy();
    expect(screen.getByRole('link', { name: /go to sign in/i })).toBeTruthy();
  });

  it('shows resend email form when verification fails', async () => {
    await setup({ error: 'Token expired or invalid' });
    expect(screen.getByRole('alert')).toBeTruthy();
    expect(screen.getByRole('button', { name: /resend verification email/i })).toBeTruthy();
  });

  it('shows resend success state when emailVerificationSent is true', async () => {
    await setup({ emailVerificationSent: true });
    expect(screen.getByText(/verification email sent!/i)).toBeTruthy();
  });

  it('shows error message when no token in URL', async () => {
    await setup({}, {});
    expect(screen.getByRole('alert')).toBeTruthy();
    expect(screen.getByText(/no verification token/i)).toBeTruthy();
  });
});

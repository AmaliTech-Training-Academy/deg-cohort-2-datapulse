import { authReducer } from './auth.reducer';
import { AuthState } from '../auth.models';
import * as AuthActions from './auth.actions';

const mockUser = {
  id: '1',
  email: 'user@example.com',
  first_name: 'Test',
  last_name: 'User',
  role: 'user' as const,
  created_at: '2026-06-03T00:00:00Z',
  is_email_verified: true,
};

const initialState: AuthState = {
  user: null,
  loading: false,
  error: null,
  forgotPasswordSent: false,
  registrationComplete: false,
  emailVerificationSent: false,
  emailVerified: false,
  passwordResetSuccess: false,
};

describe('authReducer', () => {
  it('returns initial state for unknown action', () => {
    const state = authReducer(undefined, { type: '@@INIT' } as any);
    expect(state).toEqual(initialState);
  });

  describe('login', () => {
    it('sets loading true and clears error on login', () => {
      const prev: AuthState = { ...initialState, error: 'prev error', forgotPasswordSent: true };
      const state = authReducer(prev, AuthActions.login({ email: 'a@b.com', password: 'pw' }));
      expect(state.loading).toBe(true);
      expect(state.error).toBeNull();
    });

    it('sets user and clears loading on loginSuccess', () => {
      const prev: AuthState = { ...initialState, loading: true };
      const state = authReducer(
        prev,
        AuthActions.loginSuccess({ user: mockUser, access: 'acc', refresh: 'ref' }),
      );
      expect(state.user).toEqual(mockUser);
      expect(state.loading).toBe(false);
    });

    it('sets error and clears loading on loginFailure', () => {
      const prev: AuthState = { ...initialState, loading: true };
      const state = authReducer(prev, AuthActions.loginFailure({ error: 'Bad credentials' }));
      expect(state.error).toBe('Bad credentials');
      expect(state.loading).toBe(false);
    });
  });

  describe('register', () => {
    it('sets loading true and clears error on register', () => {
      const state = authReducer(
        initialState,
        AuthActions.register({
          first_name: 'Test',
          last_name: 'User',
          email: 'a@b.com',
          password: 'pw12345',
        }),
      );
      expect(state.loading).toBe(true);
      expect(state.error).toBeNull();
      expect(state.registrationComplete).toBe(false);
    });

    it('sets registrationComplete and does NOT set user on registerSuccess', () => {
      const prev: AuthState = { ...initialState, loading: true };
      const state = authReducer(prev, AuthActions.registerSuccess({ user: mockUser }));
      expect(state.registrationComplete).toBe(true);
      expect(state.user).toBeNull();
      expect(state.loading).toBe(false);
    });

    it('sets error and clears loading on registerFailure', () => {
      const prev: AuthState = { ...initialState, loading: true };
      const state = authReducer(prev, AuthActions.registerFailure({ error: 'Email taken' }));
      expect(state.error).toBe('Email taken');
      expect(state.loading).toBe(false);
    });
  });

  describe('forgotPassword', () => {
    it('sets loading true and clears error and forgotPasswordSent', () => {
      const prev: AuthState = { ...initialState, error: 'prev', forgotPasswordSent: true };
      const state = authReducer(prev, AuthActions.forgotPassword({ email: 'a@b.com' }));
      expect(state.loading).toBe(true);
      expect(state.error).toBeNull();
      expect(state.forgotPasswordSent).toBe(false);
    });

    it('sets forgotPasswordSent true and clears loading on success', () => {
      const prev: AuthState = { ...initialState, loading: true };
      const state = authReducer(prev, AuthActions.forgotPasswordSuccess());
      expect(state.forgotPasswordSent).toBe(true);
      expect(state.loading).toBe(false);
    });

    it('sets error and clears loading on failure', () => {
      const prev: AuthState = { ...initialState, loading: true };
      const state = authReducer(prev, AuthActions.forgotPasswordFailure({ error: 'Not found' }));
      expect(state.error).toBe('Not found');
      expect(state.loading).toBe(false);
    });
  });

  describe('resendVerification', () => {
    it('sets loading true on resendVerification', () => {
      const state = authReducer(initialState, AuthActions.resendVerification({ email: 'a@b.com' }));
      expect(state.loading).toBe(true);
      expect(state.emailVerificationSent).toBe(false);
    });

    it('sets emailVerificationSent on success', () => {
      const prev: AuthState = { ...initialState, loading: true };
      const state = authReducer(prev, AuthActions.resendVerificationSuccess());
      expect(state.emailVerificationSent).toBe(true);
      expect(state.loading).toBe(false);
    });

    it('sets error on failure', () => {
      const prev: AuthState = { ...initialState, loading: true };
      const state = authReducer(
        prev,
        AuthActions.resendVerificationFailure({ error: 'Rate limited' }),
      );
      expect(state.error).toBe('Rate limited');
      expect(state.loading).toBe(false);
    });
  });

  describe('verifyEmail', () => {
    it('sets loading true on verifyEmail', () => {
      const state = authReducer(initialState, AuthActions.verifyEmail({ token: 'abc' }));
      expect(state.loading).toBe(true);
      expect(state.emailVerified).toBe(false);
    });

    it('sets emailVerified on success', () => {
      const prev: AuthState = { ...initialState, loading: true };
      const state = authReducer(prev, AuthActions.verifyEmailSuccess());
      expect(state.emailVerified).toBe(true);
      expect(state.loading).toBe(false);
    });

    it('sets error on failure', () => {
      const prev: AuthState = { ...initialState, loading: true };
      const state = authReducer(prev, AuthActions.verifyEmailFailure({ error: 'Token expired' }));
      expect(state.error).toBe('Token expired');
      expect(state.loading).toBe(false);
    });
  });

  describe('resetPassword', () => {
    it('sets loading true on resetPassword', () => {
      const state = authReducer(
        initialState,
        AuthActions.resetPassword({ uid: 'u1', token: 't1', password: 'newpw' }),
      );
      expect(state.loading).toBe(true);
      expect(state.passwordResetSuccess).toBe(false);
    });

    it('sets passwordResetSuccess on success', () => {
      const prev: AuthState = { ...initialState, loading: true };
      const state = authReducer(prev, AuthActions.resetPasswordSuccess());
      expect(state.passwordResetSuccess).toBe(true);
      expect(state.loading).toBe(false);
    });

    it('sets error on failure', () => {
      const prev: AuthState = { ...initialState, loading: true };
      const state = authReducer(prev, AuthActions.resetPasswordFailure({ error: 'Invalid token' }));
      expect(state.error).toBe('Invalid token');
      expect(state.loading).toBe(false);
    });
  });

  describe('logout', () => {
    it('resets to initial state', () => {
      const populated: AuthState = {
        ...initialState,
        user: mockUser,
        error: 'some error',
        forgotPasswordSent: true,
        registrationComplete: true,
      };
      const state = authReducer(populated, AuthActions.logout());
      expect(state).toEqual(initialState);
    });
  });
});

import { authReducer } from './auth.reducer';
import { AuthState } from '../auth.models';
import * as AuthActions from './auth.actions';

const mockUser = { id: '1', email: 'user@example.com', name: 'Test User' };

const initialState: AuthState = {
  user: null,
  loading: false,
  error: null,
  forgotPasswordSent: false,
};

describe('authReducer', () => {
  it('returns initial state for unknown action', () => {
    const state = authReducer(undefined, { type: '@@INIT' } as any);
    expect(state).toEqual(initialState);
  });

  describe('login / register', () => {
    it('sets loading true and clears error on login', () => {
      const prev: AuthState = { ...initialState, error: 'prev error', forgotPasswordSent: true };
      const state = authReducer(prev, AuthActions.login({ email: 'a@b.com', password: 'pw' }));
      expect(state.loading).toBe(true);
      expect(state.error).toBeNull();
      expect(state.forgotPasswordSent).toBe(false);
    });

    it('sets loading true on register', () => {
      const state = authReducer(
        initialState,
        AuthActions.register({ name: 'Test User', email: 'a@b.com', password: 'pw12345' }),
      );
      expect(state.loading).toBe(true);
      expect(state.error).toBeNull();
    });
  });

  describe('loginSuccess / registerSuccess', () => {
    it('sets user and clears loading on loginSuccess', () => {
      const prev: AuthState = { ...initialState, loading: true };
      const state = authReducer(prev, AuthActions.loginSuccess({ user: mockUser, token: 'tok' }));
      expect(state.user).toEqual(mockUser);
      expect(state.loading).toBe(false);
    });

    it('sets user and clears loading on registerSuccess', () => {
      const prev: AuthState = { ...initialState, loading: true };
      const state = authReducer(
        prev,
        AuthActions.registerSuccess({ user: mockUser, token: 'tok' }),
      );
      expect(state.user).toEqual(mockUser);
      expect(state.loading).toBe(false);
    });
  });

  describe('loginFailure / registerFailure', () => {
    it('sets error and clears loading on loginFailure', () => {
      const prev: AuthState = { ...initialState, loading: true };
      const state = authReducer(prev, AuthActions.loginFailure({ error: 'Bad credentials' }));
      expect(state.error).toBe('Bad credentials');
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
  });

  describe('forgotPasswordSuccess', () => {
    it('sets forgotPasswordSent true and clears loading', () => {
      const prev: AuthState = { ...initialState, loading: true };
      const state = authReducer(prev, AuthActions.forgotPasswordSuccess());
      expect(state.forgotPasswordSent).toBe(true);
      expect(state.loading).toBe(false);
    });
  });

  describe('forgotPasswordFailure', () => {
    it('sets error and clears loading', () => {
      const prev: AuthState = { ...initialState, loading: true };
      const state = authReducer(prev, AuthActions.forgotPasswordFailure({ error: 'Not found' }));
      expect(state.error).toBe('Not found');
      expect(state.loading).toBe(false);
    });
  });

  describe('logout', () => {
    it('resets to initial state', () => {
      const populated: AuthState = {
        user: mockUser,
        loading: false,
        error: 'some error',
        forgotPasswordSent: true,
      };
      const state = authReducer(populated, AuthActions.logout());
      expect(state).toEqual(initialState);
    });
  });
});

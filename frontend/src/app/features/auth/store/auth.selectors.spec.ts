import * as selectors from './auth.selectors';
import { AuthState } from '../auth.models';

const mockUser = { id: '1', email: 'user@example.com', name: 'Test User' };

function makeState(override: Partial<AuthState> = {}): { auth: AuthState } {
  return {
    auth: {
      user: null,
      loading: false,
      error: null,
      forgotPasswordSent: false,
      ...override,
    },
  };
}

describe('Auth Selectors', () => {
  describe('selectUser', () => {
    it('returns null when no user', () => {
      expect(selectors.selectUser(makeState())).toBeNull();
    });

    it('returns the current user', () => {
      expect(selectors.selectUser(makeState({ user: mockUser }))).toEqual(mockUser);
    });
  });

  describe('selectAuthLoading', () => {
    it('returns false by default', () => {
      expect(selectors.selectAuthLoading(makeState())).toBe(false);
    });

    it('returns true when loading', () => {
      expect(selectors.selectAuthLoading(makeState({ loading: true }))).toBe(true);
    });
  });

  describe('selectAuthError', () => {
    it('returns null when no error', () => {
      expect(selectors.selectAuthError(makeState())).toBeNull();
    });

    it('returns the error string', () => {
      expect(selectors.selectAuthError(makeState({ error: 'Bad credentials' }))).toBe(
        'Bad credentials',
      );
    });
  });

  describe('selectIsAuthenticated', () => {
    it('returns false when user is null', () => {
      expect(selectors.selectIsAuthenticated(makeState())).toBe(false);
    });

    it('returns true when user exists', () => {
      expect(selectors.selectIsAuthenticated(makeState({ user: mockUser }))).toBe(true);
    });
  });

  describe('selectForgotPasswordSent', () => {
    it('returns false by default', () => {
      expect(selectors.selectForgotPasswordSent(makeState())).toBe(false);
    });

    it('returns true when password reset email was sent', () => {
      expect(selectors.selectForgotPasswordSent(makeState({ forgotPasswordSent: true }))).toBe(true);
    });
  });
});

import { ReplaySubject } from 'rxjs';
import { of, throwError } from 'rxjs';
import { Action } from '@ngrx/store';
import * as AuthActions from './auth.actions';
import {
  loginEffect,
  registerEffect,
  forgotPasswordEffect,
  resendVerificationEffect,
  verifyEmailEffect,
  resetPasswordEffect,
  saveTokenEffect,
  redirectAfterAuthEffect,
  logoutEffect,
} from './auth.effects';
import { ACCESS_TOKEN_KEY, AUTH_USER_KEY, REFRESH_TOKEN_KEY } from '../auth.models';

const mockUser = {
  id: '1',
  email: 'user@example.com',
  first_name: 'Test',
  last_name: 'User',
  role: 'user' as const,
  created_at: '2026-06-03T00:00:00Z',
  is_email_verified: true,
};
const mockAdmin = {
  ...mockUser,
  id: '2',
  email: 'admin@example.com',
  role: 'admin' as const,
};

function makeActions(...actions: Action[]): ReplaySubject<Action> {
  const subject = new ReplaySubject<Action>(actions.length);
  actions.forEach((a) => subject.next(a));
  return subject;
}

describe('loginEffect', () => {
  it('emits loginSuccess on successful login', (done) => {
    const response = { user: mockUser, access: 'acc-tok', refresh: 'ref-tok' };
    const actions$ = makeActions(AuthActions.login({ email: 'a@b.com', password: 'pw' }));
    const authService = { login: jest.fn().mockReturnValue(of(response)) };

    loginEffect(actions$ as any, authService as any).subscribe((action) => {
      expect(action).toEqual(AuthActions.loginSuccess(response));
      done();
    });
  });

  it('emits loginFailure on error', (done) => {
    const actions$ = makeActions(AuthActions.login({ email: 'a@b.com', password: 'pw' }));
    const authService = {
      login: jest.fn().mockReturnValue(throwError(() => new Error('Bad credentials'))),
    };

    loginEffect(actions$ as any, authService as any).subscribe((action) => {
      expect(action).toEqual(AuthActions.loginFailure({ error: 'Bad credentials' }));
      done();
    });
  });
});

describe('registerEffect', () => {
  it('emits registerSuccess (user only, no token) on successful registration', (done) => {
    const actions$ = makeActions(
      AuthActions.register({
        first_name: 'Test',
        last_name: 'User',
        email: 'a@b.com',
        password: 'pw12345',
      }),
    );
    const authService = { register: jest.fn().mockReturnValue(of(mockUser)) };

    registerEffect(actions$ as any, authService as any).subscribe((action) => {
      expect(action).toEqual(AuthActions.registerSuccess({ user: mockUser }));
      done();
    });
  });

  it('emits registerFailure on error', (done) => {
    const actions$ = makeActions(
      AuthActions.register({
        first_name: 'Test',
        last_name: 'User',
        email: 'a@b.com',
        password: 'pw12345',
      }),
    );
    const authService = {
      register: jest.fn().mockReturnValue(throwError(() => new Error('Email already in use'))),
    };

    registerEffect(actions$ as any, authService as any).subscribe((action) => {
      expect(action).toEqual(AuthActions.registerFailure({ error: 'Email already in use' }));
      done();
    });
  });
});

describe('forgotPasswordEffect', () => {
  it('emits forgotPasswordSuccess on success', (done) => {
    const actions$ = makeActions(AuthActions.forgotPassword({ email: 'a@b.com' }));
    const authService = { forgotPassword: jest.fn().mockReturnValue(of(undefined)) };

    forgotPasswordEffect(actions$ as any, authService as any).subscribe((action) => {
      expect(action).toEqual(AuthActions.forgotPasswordSuccess());
      done();
    });
  });

  it('emits forgotPasswordFailure on error', (done) => {
    const actions$ = makeActions(AuthActions.forgotPassword({ email: 'a@b.com' }));
    const authService = {
      forgotPassword: jest.fn().mockReturnValue(throwError(() => new Error('Not found'))),
    };

    forgotPasswordEffect(actions$ as any, authService as any).subscribe((action) => {
      expect(action).toEqual(AuthActions.forgotPasswordFailure({ error: 'Not found' }));
      done();
    });
  });
});

describe('resendVerificationEffect', () => {
  it('emits resendVerificationSuccess on success', (done) => {
    const actions$ = makeActions(AuthActions.resendVerification({ email: 'a@b.com' }));
    const authService = { resendVerification: jest.fn().mockReturnValue(of(undefined)) };

    resendVerificationEffect(actions$ as any, authService as any).subscribe((action) => {
      expect(action).toEqual(AuthActions.resendVerificationSuccess());
      done();
    });
  });

  it('emits resendVerificationFailure on error', (done) => {
    const actions$ = makeActions(AuthActions.resendVerification({ email: 'a@b.com' }));
    const authService = {
      resendVerification: jest.fn().mockReturnValue(throwError(() => new Error('Rate limited'))),
    };

    resendVerificationEffect(actions$ as any, authService as any).subscribe((action) => {
      expect(action).toEqual(
        AuthActions.resendVerificationFailure({ error: 'Rate limited' }),
      );
      done();
    });
  });
});

describe('verifyEmailEffect', () => {
  it('emits verifyEmailSuccess on success', (done) => {
    const actions$ = makeActions(AuthActions.verifyEmail({ token: 'abc-token' }));
    const authService = { verifyEmail: jest.fn().mockReturnValue(of(undefined)) };

    verifyEmailEffect(actions$ as any, authService as any).subscribe((action) => {
      expect(action).toEqual(AuthActions.verifyEmailSuccess());
      done();
    });
  });

  it('emits verifyEmailFailure on error', (done) => {
    const actions$ = makeActions(AuthActions.verifyEmail({ token: 'bad-token' }));
    const authService = {
      verifyEmail: jest.fn().mockReturnValue(throwError(() => new Error('Token expired'))),
    };

    verifyEmailEffect(actions$ as any, authService as any).subscribe((action) => {
      expect(action).toEqual(AuthActions.verifyEmailFailure({ error: 'Token expired' }));
      done();
    });
  });
});

describe('resetPasswordEffect', () => {
  it('emits resetPasswordSuccess on success', (done) => {
    const actions$ = makeActions(
      AuthActions.resetPassword({ uid: 'u1', token: 't1', password: 'newpw' }),
    );
    const authService = { resetPassword: jest.fn().mockReturnValue(of(undefined)) };

    resetPasswordEffect(actions$ as any, authService as any).subscribe((action) => {
      expect(action).toEqual(AuthActions.resetPasswordSuccess());
      done();
    });
  });

  it('emits resetPasswordFailure on error', (done) => {
    const actions$ = makeActions(
      AuthActions.resetPassword({ uid: 'u1', token: 'bad', password: 'newpw' }),
    );
    const authService = {
      resetPassword: jest.fn().mockReturnValue(throwError(() => new Error('Invalid token'))),
    };

    resetPasswordEffect(actions$ as any, authService as any).subscribe((action) => {
      expect(action).toEqual(AuthActions.resetPasswordFailure({ error: 'Invalid token' }));
      done();
    });
  });
});

describe('saveTokenEffect', () => {
  afterEach(() => {
    localStorage.clear();
    jest.restoreAllMocks();
  });

  it('saves access and refresh tokens and user to localStorage on loginSuccess', (done) => {
    const setItemSpy = jest.spyOn(Storage.prototype, 'setItem');
    const actions$ = makeActions(
      AuthActions.loginSuccess({ user: mockUser, access: 'acc-tok', refresh: 'ref-tok' }),
    );

    saveTokenEffect(actions$ as any).subscribe(() => {
      expect(setItemSpy).toHaveBeenCalledWith(ACCESS_TOKEN_KEY, 'acc-tok');
      expect(setItemSpy).toHaveBeenCalledWith(REFRESH_TOKEN_KEY, 'ref-tok');
      expect(setItemSpy).toHaveBeenCalledWith(AUTH_USER_KEY, JSON.stringify(mockUser));
      done();
    });
  });

  it('does NOT fire on registerSuccess (user must verify email before logging in)', () => {
    const setItemSpy = jest.spyOn(Storage.prototype, 'setItem');
    const actions$ = makeActions(AuthActions.registerSuccess({ user: mockUser }));
    let emitted = false;
    saveTokenEffect(actions$ as any).subscribe(() => {
      emitted = true;
    });
    expect(emitted).toBe(false);
    expect(setItemSpy).not.toHaveBeenCalled();
  });
});

describe('redirectAfterAuthEffect', () => {
  it('navigates to /dashboard/projects on loginSuccess for a regular user', (done) => {
    const router = { navigate: jest.fn() };
    const actions$ = makeActions(
      AuthActions.loginSuccess({ user: mockUser, access: 'acc', refresh: 'ref' }),
    );

    redirectAfterAuthEffect(actions$ as any, router as any).subscribe(() => {
      expect(router.navigate).toHaveBeenCalledWith(['/dashboard/projects']);
      done();
    });
  });

  it('navigates to /dashboard/overview on loginSuccess for an admin', (done) => {
    const router = { navigate: jest.fn() };
    const actions$ = makeActions(
      AuthActions.loginSuccess({ user: mockAdmin, access: 'acc', refresh: 'ref' }),
    );

    redirectAfterAuthEffect(actions$ as any, router as any).subscribe(() => {
      expect(router.navigate).toHaveBeenCalledWith(['/dashboard/overview']);
      done();
    });
  });

  it('does NOT redirect on registerSuccess (user must verify email first)', () => {
    const router = { navigate: jest.fn() };
    const actions$ = makeActions(AuthActions.registerSuccess({ user: mockUser }));
    let emitted = false;
    redirectAfterAuthEffect(actions$ as any, router as any).subscribe(() => { emitted = true; });
    expect(emitted).toBe(false);
    expect(router.navigate).not.toHaveBeenCalled();
  });
});

describe('logoutEffect', () => {
  afterEach(() => localStorage.clear());

  it('removes access token, refresh token, and user from localStorage on logout', (done) => {
    localStorage.setItem(ACCESS_TOKEN_KEY, 'acc-tok');
    localStorage.setItem(REFRESH_TOKEN_KEY, 'ref-tok');
    const router = { navigate: jest.fn() };
    const actions$ = makeActions(AuthActions.logout());

    logoutEffect(actions$ as any, router as any).subscribe(() => {
      expect(localStorage.getItem(ACCESS_TOKEN_KEY)).toBeNull();
      expect(localStorage.getItem(REFRESH_TOKEN_KEY)).toBeNull();
      expect(router.navigate).toHaveBeenCalledWith(['/login']);
      done();
    });
  });
});

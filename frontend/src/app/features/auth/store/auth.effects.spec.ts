import { ReplaySubject } from 'rxjs';
import { of, throwError } from 'rxjs';
import { Action } from '@ngrx/store';
import * as AuthActions from './auth.actions';
import {
  loginEffect,
  registerEffect,
  forgotPasswordEffect,
  saveTokenEffect,
  redirectAfterAuthEffect,
  logoutEffect,
} from './auth.effects';
import { AUTH_TOKEN_KEY } from '../auth.models';

const mockUser = { id: '1', email: 'user@example.com', name: 'Test User' };

function makeActions(...actions: Action[]): ReplaySubject<Action> {
  const subject = new ReplaySubject<Action>(actions.length);
  actions.forEach((a) => subject.next(a));
  return subject;
}

describe('loginEffect', () => {
  it('emits loginSuccess on successful login', (done) => {
    const response = { user: mockUser, token: 'tok-123' };
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
  it('emits registerSuccess on successful registration', (done) => {
    const response = { user: mockUser, token: 'tok-456' };
    const actions$ = makeActions(
      AuthActions.register({ name: 'Test User', email: 'a@b.com', password: 'pw12345' }),
    );
    const authService = { register: jest.fn().mockReturnValue(of(response)) };

    registerEffect(actions$ as any, authService as any).subscribe((action) => {
      expect(action).toEqual(AuthActions.registerSuccess(response));
      done();
    });
  });

  it('emits registerFailure on error', (done) => {
    const actions$ = makeActions(
      AuthActions.register({ name: 'Test User', email: 'a@b.com', password: 'pw12345' }),
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

describe('saveTokenEffect', () => {
  afterEach(() => localStorage.clear());

  it('saves token to localStorage on loginSuccess', (done) => {
    const setItemSpy = jest.spyOn(Storage.prototype, 'setItem');
    const actions$ = makeActions(AuthActions.loginSuccess({ user: mockUser, token: 'save-me' }));

    saveTokenEffect(actions$ as any).subscribe(() => {
      expect(setItemSpy).toHaveBeenCalledWith(AUTH_TOKEN_KEY, 'save-me');
      done();
    });
  });

  it('saves token on registerSuccess', (done) => {
    const setItemSpy = jest.spyOn(Storage.prototype, 'setItem');
    const actions$ = makeActions(
      AuthActions.registerSuccess({ user: mockUser, token: 'reg-token' }),
    );

    saveTokenEffect(actions$ as any).subscribe(() => {
      expect(setItemSpy).toHaveBeenCalledWith(AUTH_TOKEN_KEY, 'reg-token');
      done();
    });
  });
});

describe('redirectAfterAuthEffect', () => {
  it('navigates to /dashboard on loginSuccess', (done) => {
    const router = { navigate: jest.fn() };
    const actions$ = makeActions(AuthActions.loginSuccess({ user: mockUser, token: 'tok' }));

    redirectAfterAuthEffect(actions$ as any, router as any).subscribe(() => {
      expect(router.navigate).toHaveBeenCalledWith(['/dashboard']);
      done();
    });
  });

  it('navigates to /dashboard on registerSuccess', (done) => {
    const router = { navigate: jest.fn() };
    const actions$ = makeActions(AuthActions.registerSuccess({ user: mockUser, token: 'tok' }));

    redirectAfterAuthEffect(actions$ as any, router as any).subscribe(() => {
      expect(router.navigate).toHaveBeenCalledWith(['/dashboard']);
      done();
    });
  });
});

describe('logoutEffect', () => {
  afterEach(() => localStorage.clear());

  it('removes token and navigates to /login on logout', (done) => {
    localStorage.setItem(AUTH_TOKEN_KEY, 'existing-token');
    const router = { navigate: jest.fn() };
    const actions$ = makeActions(AuthActions.logout());

    logoutEffect(actions$ as any, router as any).subscribe(() => {
      expect(localStorage.getItem(AUTH_TOKEN_KEY)).toBeNull();
      expect(router.navigate).toHaveBeenCalledWith(['/login']);
      done();
    });
  });
});

import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { Actions, createEffect, ofType, ROOT_EFFECTS_INIT } from '@ngrx/effects';
import { catchError, map, switchMap, tap } from 'rxjs/operators';
import { of } from 'rxjs';
import * as AuthActions from './auth.actions';
import { AuthService } from '../auth.service';
import { ACCESS_TOKEN_KEY, AUTH_USER_KEY, REFRESH_TOKEN_KEY, User } from '../auth.models';

export const loginEffect = createEffect(
  (actions$ = inject(Actions), authService = inject(AuthService)) =>
    actions$.pipe(
      ofType(AuthActions.login),
      switchMap(({ email, password }) =>
        authService.login(email, password).pipe(
          map(({ user, access, refresh }) =>
            AuthActions.loginSuccess({ user, access, refresh }),
          ),
          catchError((err) => of(AuthActions.loginFailure({ error: err.message }))),
        ),
      ),
    ),
  { functional: true },
);

export const registerEffect = createEffect(
  (actions$ = inject(Actions), authService = inject(AuthService)) =>
    actions$.pipe(
      ofType(AuthActions.register),
      switchMap(({ email, first_name, last_name, password }) =>
        authService.register(email, first_name, last_name, password).pipe(
          map((user) => AuthActions.registerSuccess({ user })),
          catchError((err) => of(AuthActions.registerFailure({ error: err.message }))),
        ),
      ),
    ),
  { functional: true },
);

export const forgotPasswordEffect = createEffect(
  (actions$ = inject(Actions), authService = inject(AuthService)) =>
    actions$.pipe(
      ofType(AuthActions.forgotPassword),
      switchMap(({ email }) =>
        authService.forgotPassword(email).pipe(
          map(() => AuthActions.forgotPasswordSuccess()),
          catchError((err) => of(AuthActions.forgotPasswordFailure({ error: err.message }))),
        ),
      ),
    ),
  { functional: true },
);

export const resendVerificationEffect = createEffect(
  (actions$ = inject(Actions), authService = inject(AuthService)) =>
    actions$.pipe(
      ofType(AuthActions.resendVerification),
      switchMap(({ email }) =>
        authService.resendVerification(email).pipe(
          map(() => AuthActions.resendVerificationSuccess()),
          catchError((err) =>
            of(AuthActions.resendVerificationFailure({ error: err.message })),
          ),
        ),
      ),
    ),
  { functional: true },
);

export const verifyEmailEffect = createEffect(
  (actions$ = inject(Actions), authService = inject(AuthService)) =>
    actions$.pipe(
      ofType(AuthActions.verifyEmail),
      switchMap(({ token }) =>
        authService.verifyEmail(token).pipe(
          map(() => AuthActions.verifyEmailSuccess()),
          catchError((err) => of(AuthActions.verifyEmailFailure({ error: err.message }))),
        ),
      ),
    ),
  { functional: true },
);

export const resetPasswordEffect = createEffect(
  (actions$ = inject(Actions), authService = inject(AuthService)) =>
    actions$.pipe(
      ofType(AuthActions.resetPassword),
      switchMap(({ uid, token, password }) =>
        authService.resetPassword(uid, token, password).pipe(
          map(() => AuthActions.resetPasswordSuccess()),
          catchError((err) => of(AuthActions.resetPasswordFailure({ error: err.message }))),
        ),
      ),
    ),
  { functional: true },
);

export const saveTokenEffect = createEffect(
  (actions$ = inject(Actions)) =>
    actions$.pipe(
      ofType(AuthActions.loginSuccess),
      tap(({ access, refresh, user }) => {
        localStorage.setItem(ACCESS_TOKEN_KEY, access);
        localStorage.setItem(REFRESH_TOKEN_KEY, refresh);
        localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user));
      }),
    ),
  { functional: true, dispatch: false },
);

export const redirectAfterAuthEffect = createEffect(
  (actions$ = inject(Actions), router = inject(Router)) =>
    actions$.pipe(
      ofType(AuthActions.loginSuccess),
      tap(({ user }) => {
        const url = user.role === 'admin' ? '/dashboard/overview' : '/dashboard/projects';
        router.navigate([url]);
      }),
    ),
  { functional: true, dispatch: false },
);

export const initAuthEffect = createEffect(
  (actions$ = inject(Actions)) =>
    actions$.pipe(
      ofType(ROOT_EFFECTS_INIT),
      map(() => {
        // Clean up legacy mock token from old implementation
        localStorage.removeItem('auth_token');

        const token = localStorage.getItem(ACCESS_TOKEN_KEY);
        const userJson = localStorage.getItem(AUTH_USER_KEY);
        if (token && userJson) {
          try {
            const user = JSON.parse(userJson) as User;
            return AuthActions.restoreSession({ user });
          } catch {
            return AuthActions.restoreSessionEmpty();
          }
        }
        return AuthActions.restoreSessionEmpty();
      }),
    ),
  { functional: true },
);

export const logoutEffect = createEffect(
  (actions$ = inject(Actions), router = inject(Router)) =>
    actions$.pipe(
      ofType(AuthActions.logout),
      tap(() => {
        localStorage.removeItem(ACCESS_TOKEN_KEY);
        localStorage.removeItem(REFRESH_TOKEN_KEY);
        localStorage.removeItem(AUTH_USER_KEY);
        router.navigate(['/login']);
      }),
    ),
  { functional: true, dispatch: false },
);

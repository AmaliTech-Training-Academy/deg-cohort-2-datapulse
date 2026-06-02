import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { Actions, createEffect, ofType, ROOT_EFFECTS_INIT } from '@ngrx/effects';
import { catchError, map, switchMap, tap } from 'rxjs/operators';
import { of } from 'rxjs';
import * as AuthActions from './auth.actions';
import { AuthService } from '../auth.service';
import { AUTH_TOKEN_KEY, AUTH_USER_KEY, User } from '../auth.models';

export const loginEffect = createEffect(
  (actions$ = inject(Actions), authService = inject(AuthService)) =>
    actions$.pipe(
      ofType(AuthActions.login),
      switchMap(({ email, password }) =>
        authService.login(email, password).pipe(
          map(({ user, token }) => AuthActions.loginSuccess({ user, token })),
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
      switchMap(({ name, email, password }) =>
        authService.register(name, email, password).pipe(
          map(({ user, token }) => AuthActions.registerSuccess({ user, token })),
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

export const saveTokenEffect = createEffect(
  (actions$ = inject(Actions)) =>
    actions$.pipe(
      ofType(AuthActions.loginSuccess, AuthActions.registerSuccess),
      tap(({ token, user }) => {
        localStorage.setItem(AUTH_TOKEN_KEY, token);
        localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user));
      }),
    ),
  { functional: true, dispatch: false },
);

export const redirectAfterAuthEffect = createEffect(
  (actions$ = inject(Actions), router = inject(Router)) =>
    actions$.pipe(
      ofType(AuthActions.loginSuccess, AuthActions.registerSuccess),
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
        const token = localStorage.getItem(AUTH_TOKEN_KEY);
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
        localStorage.removeItem(AUTH_TOKEN_KEY);
        localStorage.removeItem(AUTH_USER_KEY);
        router.navigate(['/login']);
      }),
    ),
  { functional: true, dispatch: false },
);

import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { catchError, map, switchMap, tap } from 'rxjs/operators';
import { of } from 'rxjs';
import * as AuthActions from './auth.actions';
import { AuthService } from '../auth.service';
import { AUTH_TOKEN_KEY } from '../auth.models';

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

export const saveTokenEffect = createEffect(
  (actions$ = inject(Actions)) =>
    actions$.pipe(
      ofType(AuthActions.loginSuccess, AuthActions.registerSuccess),
      tap(({ token }) => localStorage.setItem(AUTH_TOKEN_KEY, token)),
    ),
  { functional: true, dispatch: false },
);

export const redirectAfterAuthEffect = createEffect(
  (actions$ = inject(Actions), router = inject(Router)) =>
    actions$.pipe(
      ofType(AuthActions.loginSuccess, AuthActions.registerSuccess),
      tap(() => router.navigate(['/dashboard'])),
    ),
  { functional: true, dispatch: false },
);

export const logoutEffect = createEffect(
  (actions$ = inject(Actions), router = inject(Router)) =>
    actions$.pipe(
      ofType(AuthActions.logout),
      tap(() => {
        localStorage.removeItem(AUTH_TOKEN_KEY);
        router.navigate(['/login']);
      }),
    ),
  { functional: true, dispatch: false },
);

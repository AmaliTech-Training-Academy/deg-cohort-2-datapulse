import { HttpClient, HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { throwError } from 'rxjs';
import { catchError, switchMap } from 'rxjs/operators';
import {
  ACCESS_TOKEN_KEY,
  AUTH_USER_KEY,
  RefreshResponse,
  REFRESH_TOKEN_KEY,
} from '../../features/auth/auth.models';
import { environment } from '../../../environments/environment';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const token = localStorage.getItem(ACCESS_TOKEN_KEY);
  const authed = token ? req.clone({ setHeaders: { Authorization: `Bearer ${token}` } }) : req;

  return next(authed).pipe(
    catchError((error: HttpErrorResponse) => {
      // Only attempt refresh on 401; skip if this IS the refresh request (prevent infinite loop)
      const isRefreshCall = req.url.includes('/auth/refresh');
      if (error.status === 401 && !isRefreshCall) {
        const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
        if (refreshToken) {
          const http = inject(HttpClient);
          const router = inject(Router);
          return http
            .post<RefreshResponse>(`${environment.apiUrl}/v1/auth/refresh/`, {
              refresh: refreshToken,
            })
            .pipe(
              switchMap(({ access, refresh }) => {
                localStorage.setItem(ACCESS_TOKEN_KEY, access);
                localStorage.setItem(REFRESH_TOKEN_KEY, refresh);
                return next(
                  req.clone({ setHeaders: { Authorization: `Bearer ${access}` } }),
                );
              }),
              catchError((refreshErr) => {
                localStorage.removeItem(ACCESS_TOKEN_KEY);
                localStorage.removeItem(REFRESH_TOKEN_KEY);
                localStorage.removeItem(AUTH_USER_KEY);
                router.navigate(['/login']);
                return throwError(() => refreshErr);
              }),
            );
        }
      }
      return throwError(() => error);
    }),
  );
};

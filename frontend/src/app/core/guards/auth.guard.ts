import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AUTH_TOKEN_KEY } from '../../features/auth/auth.models';

export const authGuard: CanActivateFn = () => {
  const router = inject(Router);
  return localStorage.getItem(AUTH_TOKEN_KEY) ? true : router.createUrlTree(['/login']);
};

import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { ACCESS_TOKEN_KEY } from '../../features/auth/auth.models';

export const authGuard: CanActivateFn = () => {
  const router = inject(Router);
  return localStorage.getItem(ACCESS_TOKEN_KEY) ? true : router.createUrlTree(['/login']);
};

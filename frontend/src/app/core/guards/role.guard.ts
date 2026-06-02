import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { Store } from '@ngrx/store';
import { map, take } from 'rxjs/operators';
import { UserRole } from '../../features/auth/auth.models';
import { selectUser, selectUserRole } from '../../features/auth/store/auth.selectors';

export function roleGuard(requiredRole: UserRole): CanActivateFn {
  return () => {
    const store = inject(Store);
    const router = inject(Router);
    return store.select(selectUserRole).pipe(
      take(1),
      map((role) =>
        role === requiredRole ? true : router.createUrlTree(['/dashboard']),
      ),
    );
  };
}

export const roleRedirectGuard: CanActivateFn = () => {
  const store = inject(Store);
  const router = inject(Router);
  return store.select(selectUser).pipe(
    take(1),
    map((user) => {
      if (!user) return router.createUrlTree(['/login']);
      return user.role === 'admin'
        ? router.createUrlTree(['/dashboard/overview'])
        : router.createUrlTree(['/dashboard/projects']);
    }),
  );
};

import { inject } from '@angular/core';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { catchError, map, switchMap } from 'rxjs/operators';
import { of } from 'rxjs';
import * as AdminUsersActions from './admin-users.actions';
import { DashboardApiService } from '../../services/dashboard-api.service';
import { mapAdminUser } from '../../models/admin-user.model';

export const loadAdminUsersEffect = createEffect(
  (actions$ = inject(Actions), api = inject(DashboardApiService)) =>
    actions$.pipe(
      ofType(AdminUsersActions.loadAdminUsers),
      switchMap(() =>
        api.getAdminUsers({ page_size: 100 }).pipe(
          map((res) =>
            AdminUsersActions.loadAdminUsersSuccess({
              users: res.results.map(mapAdminUser),
              total: res.count,
            }),
          ),
          catchError((err) =>
            of(AdminUsersActions.loadAdminUsersFailure({ error: err.message })),
          ),
        ),
      ),
    ),
  { functional: true },
);

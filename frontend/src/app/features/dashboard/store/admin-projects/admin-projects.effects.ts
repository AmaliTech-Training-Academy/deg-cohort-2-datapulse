import { inject } from '@angular/core';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { catchError, map, switchMap } from 'rxjs/operators';
import { of } from 'rxjs';
import * as AdminProjectsActions from './admin-projects.actions';
import { DashboardApiService } from '../../services/dashboard-api.service';
import { mapAdminDataset } from '../../models/admin-dataset.model';

export const loadAdminProjectsEffect = createEffect(
  (actions$ = inject(Actions), api = inject(DashboardApiService)) =>
    actions$.pipe(
      ofType(AdminProjectsActions.loadAdminProjects),
      switchMap(({ params }) =>
        api.getAdminDatasets({ page_size: 100, ...params }).pipe(
          map((res) =>
            AdminProjectsActions.loadAdminProjectsSuccess({
              datasets: res.results.map(mapAdminDataset),
              total: res.count,
            }),
          ),
          catchError((err) =>
            of(AdminProjectsActions.loadAdminProjectsFailure({ error: err.message })),
          ),
        ),
      ),
    ),
  { functional: true },
);

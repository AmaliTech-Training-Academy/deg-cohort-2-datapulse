import { inject } from '@angular/core';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { catchError, map, switchMap } from 'rxjs/operators';
import { of } from 'rxjs';
import * as ProjectDetailActions from './project-detail.actions';
import { DashboardApiService } from '../../services/dashboard-api.service';

export const loadProjectDetailEffect = createEffect(
  (actions$ = inject(Actions), api = inject(DashboardApiService)) =>
    actions$.pipe(
      ofType(ProjectDetailActions.loadProjectDetail),
      switchMap(({ datasetId }) =>
        api.getProject(datasetId).pipe(
          map((dataset) => ProjectDetailActions.loadProjectDetailSuccess({ dataset })),
          catchError((err) =>
            of(ProjectDetailActions.loadProjectDetailFailure({ error: err.message })),
          ),
        ),
      ),
    ),
  { functional: true },
);

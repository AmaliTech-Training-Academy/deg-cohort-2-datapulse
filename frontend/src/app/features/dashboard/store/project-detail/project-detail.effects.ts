import { inject } from '@angular/core';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { catchError, exhaustMap, map, mergeMap, switchMap } from 'rxjs/operators';
import { of } from 'rxjs';
import * as ProjectDetailActions from './project-detail.actions';
import * as ReportsActions from '../reports/reports.actions';
import * as TrendsActions from '../trends/trends.actions';
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

export const uploadVersionEffect = createEffect(
  (actions$ = inject(Actions), api = inject(DashboardApiService)) =>
    actions$.pipe(
      ofType(ProjectDetailActions.uploadVersion),
      exhaustMap(({ datasetId, file }) =>
        api.uploadNewVersion(datasetId, file).pipe(
          map(() => ProjectDetailActions.uploadVersionSuccess({ datasetId })),
          catchError((err) =>
            of(
              ProjectDetailActions.uploadVersionFailure({
                error: err.message ?? 'Upload failed.',
              }),
            ),
          ),
        ),
      ),
    ),
  { functional: true },
);

// After a successful version upload, reload project detail, reports, and trends
export const reloadAfterUploadEffect = createEffect(
  (actions$ = inject(Actions)) =>
    actions$.pipe(
      ofType(ProjectDetailActions.uploadVersionSuccess),
      mergeMap(({ datasetId }) => [
        ProjectDetailActions.loadProjectDetail({ datasetId }),
        ReportsActions.loadReports({ datasetId }),
        TrendsActions.loadTrends({ datasetId }),
      ]),
    ),
  { functional: true },
);

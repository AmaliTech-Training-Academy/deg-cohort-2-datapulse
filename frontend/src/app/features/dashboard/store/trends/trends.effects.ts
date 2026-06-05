import { inject } from '@angular/core';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { catchError, map, switchMap } from 'rxjs/operators';
import { of } from 'rxjs';
import * as TrendsActions from './trends.actions';
import { DashboardApiService } from '../../services/dashboard-api.service';
import { mapTrendPoints } from '../../models/trend.model';

export const loadTrendsEffect = createEffect(
  (actions$ = inject(Actions), api = inject(DashboardApiService)) =>
    actions$.pipe(
      ofType(TrendsActions.loadTrends),
      switchMap(({ datasetId }) =>
        api.getTrends(datasetId).pipe(
          map((points) => TrendsActions.loadTrendsSuccess({ data: mapTrendPoints(points) })),
          catchError((err) => of(TrendsActions.loadTrendsFailure({ error: err.message }))),
        ),
      ),
    ),
  { functional: true },
);

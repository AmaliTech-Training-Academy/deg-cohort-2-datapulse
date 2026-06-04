import { inject } from '@angular/core';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { catchError, map, switchMap } from 'rxjs/operators';
import { of } from 'rxjs';
import * as ReportsActions from './reports.actions';
import { DashboardApiService } from '../../services/dashboard-api.service';
import { mapReportListItem, mapReportsSummary } from '../../models/report.model';

export const loadReportsEffect = createEffect(
  (actions$ = inject(Actions), api = inject(DashboardApiService)) =>
    actions$.pipe(
      ofType(ReportsActions.loadReports),
      switchMap(({ datasetId }) =>
        api.getReports(datasetId).pipe(
          map((response) =>
            ReportsActions.loadReportsSuccess({
              reports: response.results.map(mapReportListItem),
              summary: mapReportsSummary(response),
            }),
          ),
          catchError((err) => of(ReportsActions.loadReportsFailure({ error: err.message }))),
        ),
      ),
    ),
  { functional: true },
);

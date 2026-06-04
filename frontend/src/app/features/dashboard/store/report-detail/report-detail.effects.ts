import { inject } from '@angular/core';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { catchError, map, switchMap } from 'rxjs/operators';
import { of } from 'rxjs';
import * as ReportDetailActions from './report-detail.actions';
import { DashboardApiService } from '../../services/dashboard-api.service';
import { mapReportDetail } from '../../models/report-detail.model';

export const loadReportDetailEffect = createEffect(
  (actions$ = inject(Actions), api = inject(DashboardApiService)) =>
    actions$.pipe(
      ofType(ReportDetailActions.loadReportDetail),
      switchMap(({ reportId }) =>
        api.getReportDetail(reportId).pipe(
          map((detail) =>
            ReportDetailActions.loadReportDetailSuccess({ report: mapReportDetail(detail) }),
          ),
          catchError((err) =>
            of(ReportDetailActions.loadReportDetailFailure({ error: err.message })),
          ),
        ),
      ),
    ),
  { functional: true },
);

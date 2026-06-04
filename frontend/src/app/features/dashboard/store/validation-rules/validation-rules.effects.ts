import { inject } from '@angular/core';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { Store } from '@ngrx/store';
import { catchError, exhaustMap, map, switchMap, withLatestFrom } from 'rxjs/operators';
import { of } from 'rxjs';
import * as ValidationRulesActions from './validation-rules.actions';
import { selectValidationRulesDatasetId } from './validation-rules.selectors';
import { DashboardApiService } from '../../services/dashboard-api.service';
import { mapApiRule } from '../../models/validation-rule.model';

export const loadRulesEffect = createEffect(
  (actions$ = inject(Actions), api = inject(DashboardApiService)) =>
    actions$.pipe(
      ofType(ValidationRulesActions.loadRules),
      switchMap(({ datasetId }) =>
        api.getRules(datasetId).pipe(
          map((response) =>
            ValidationRulesActions.loadRulesSuccess({
              rules: response.results.map(mapApiRule),
            }),
          ),
          catchError((err) =>
            of(
              ValidationRulesActions.loadRulesFailure({
                error: err.message ?? 'Failed to load rules.',
              }),
            ),
          ),
        ),
      ),
    ),
  { functional: true },
);

export const addRuleEffect = createEffect(
  (actions$ = inject(Actions), api = inject(DashboardApiService)) =>
    actions$.pipe(
      ofType(ValidationRulesActions.addRule),
      exhaustMap(({ datasetId, request }) =>
        api.createRule(datasetId, request).pipe(
          map((apiRule) => ValidationRulesActions.addRuleSuccess({ rule: mapApiRule(apiRule) })),
          catchError((err) =>
            of(
              ValidationRulesActions.addRuleFailure({
                error: err.message ?? 'Failed to add rule.',
              }),
            ),
          ),
        ),
      ),
    ),
  { functional: true },
);

export const deleteRuleEffect = createEffect(
  (actions$ = inject(Actions), api = inject(DashboardApiService)) =>
    actions$.pipe(
      ofType(ValidationRulesActions.deleteRule),
      exhaustMap(({ ruleId }) =>
        api.deleteRule(ruleId).pipe(
          map(() => ValidationRulesActions.deleteRuleSuccess({ ruleId })),
          catchError((err) =>
            of(
              ValidationRulesActions.deleteRuleFailure({
                error: err.message ?? 'Failed to delete rule.',
              }),
            ),
          ),
        ),
      ),
    ),
  { functional: true },
);

export const runChecksOnDatasetEffect = createEffect(
  (actions$ = inject(Actions), api = inject(DashboardApiService)) =>
    actions$.pipe(
      ofType(ValidationRulesActions.runChecksOnDataset),
      exhaustMap(({ datasetId }) =>
        api.runChecks(datasetId).pipe(
          map(() => ValidationRulesActions.runChecksOnDatasetSuccess()),
          catchError((err) =>
            of(
              ValidationRulesActions.runChecksOnDatasetFailure({
                error: err.message ?? 'Run check failed.',
              }),
            ),
          ),
        ),
      ),
    ),
  { functional: true },
);

// Reload rules after run-check so failing/passing counts reflect the latest results
export const reloadRulesAfterRunEffect = createEffect(
  (actions$ = inject(Actions), store = inject(Store)) =>
    actions$.pipe(
      ofType(ValidationRulesActions.runChecksOnDatasetSuccess),
      withLatestFrom(store.select(selectValidationRulesDatasetId)),
      map(([, datasetId]) =>
        datasetId
          ? ValidationRulesActions.loadRules({ datasetId })
          : ValidationRulesActions.clearValidationRules(),
      ),
    ),
  { functional: true },
);

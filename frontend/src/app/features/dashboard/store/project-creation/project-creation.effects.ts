import { inject } from '@angular/core';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { Store } from '@ngrx/store';
import { catchError, exhaustMap, map, withLatestFrom } from 'rxjs/operators';
import { of } from 'rxjs';
import * as ProjectCreationActions from './project-creation.actions';
import * as ProjectsActions from '../projects/projects.actions';
import { selectDatasetId } from './project-creation.selectors';
import { DashboardApiService } from '../../services/dashboard-api.service';
import { ApiRuleType, RulesBatchRequest } from '../../models/rules-batch.model';
import { SuggestedRule } from '../../../../shared/models/dashboard.models';

function toApiRuleType(type: string): ApiRuleType {
  switch (type) {
    case 'uniqueness':
    case 'unique':
    case 'uniqueness_check':
      return 'uniqueness_check';
    case 'type_check':
      return 'type_check';
    case 'range_check':
    case 'range':
      return 'range_check';
    default:
      return 'null_check';
  }
}

function toRuleConfig(type: string, params?: string): Record<string, unknown> {
  if (type === 'type_check') {
    const expectedType = params?.split(/[,\s]/)[0]?.trim() || 'string';
    return { expected_type: expectedType };
  }
  if (type === 'range_check' || type === 'range') {
    const minMatch = /min[=:\s]+(-?[\d.]+)/i.exec(params ?? '');
    const maxMatch = /max[=:\s]+(-?[\d.]+)/i.exec(params ?? '');
    return {
      min: minMatch ? parseFloat(minMatch[1]) : 0,
      max: maxMatch ? parseFloat(maxMatch[1]) : 100,
    };
  }
  return {};
}

function mapToRulesBatch(rules: SuggestedRule[]): RulesBatchRequest {
  return rules
    .filter((r) => r.enabled)
    .map((r) => ({
      column_name: r.column,
      rule_type: toApiRuleType(r.type),
      rule_config: toRuleConfig(r.type, r.params),
    }));
}

export const uploadDatasetEffect = createEffect(
  (actions$ = inject(Actions), api = inject(DashboardApiService)) =>
    actions$.pipe(
      ofType(ProjectCreationActions.uploadDataset),
      exhaustMap(({ file, fileTitle, description }) => {
        const formData = new FormData();
        formData.append('file', file);
        if (fileTitle) formData.append('file_title', fileTitle);
        if (description) formData.append('description', description);
        return api.uploadDataset(formData).pipe(
          map((res) =>
            ProjectCreationActions.uploadDatasetSuccess({
              datasetId: res.id,
              columns: res.columns,
            }),
          ),
          catchError((err) =>
            of(
              ProjectCreationActions.uploadDatasetFailure({
                error: err.message ?? 'Upload failed.',
              }),
            ),
          ),
        );
      }),
    ),
  { functional: true },
);

export const saveRulesEffect = createEffect(
  (actions$ = inject(Actions), api = inject(DashboardApiService), store = inject(Store)) =>
    actions$.pipe(
      ofType(ProjectCreationActions.saveRules),
      withLatestFrom(store.select(selectDatasetId)),
      exhaustMap(([{ rules }, datasetId]) => {
        if (!datasetId) {
          return of(ProjectCreationActions.saveRulesFailure({ error: 'Dataset not found.' }));
        }
        const payload = mapToRulesBatch(rules);
        if (payload.length === 0) {
          return of(
            ProjectCreationActions.saveRulesFailure({
              error: 'Enable at least one rule before running checks.',
            }),
          );
        }
        return api.saveRulesBatch(datasetId, payload).pipe(
          map(() => ProjectCreationActions.saveRulesSuccess()),
          catchError((err) =>
            of(
              ProjectCreationActions.saveRulesFailure({
                error: err.message ?? 'Failed to save rules.',
              }),
            ),
          ),
        );
      }),
    ),
  { functional: true },
);

export const runChecksEffect = createEffect(
  (actions$ = inject(Actions), api = inject(DashboardApiService), store = inject(Store)) =>
    actions$.pipe(
      ofType(ProjectCreationActions.runChecks),
      withLatestFrom(store.select(selectDatasetId)),
      exhaustMap(([, datasetId]) => {
        if (!datasetId) {
          return of(
            ProjectCreationActions.runChecksFailure({ error: 'No dataset to run checks on.' }),
          );
        }
        return api.runChecks(datasetId).pipe(
          map((res) =>
            ProjectCreationActions.runChecksSuccess({ score: res.overall_score ?? 0 }),
          ),
          catchError((err) =>
            of(
              ProjectCreationActions.runChecksFailure({
                error: err.message ?? 'Validation check failed.',
              }),
            ),
          ),
        );
      }),
    ),
  { functional: true },
);

// Refresh the projects list after a successful check run so the new project
// appears immediately when the user lands on /dashboard/projects.
export const refreshProjectsAfterRunEffect = createEffect(
  (actions$ = inject(Actions)) =>
    actions$.pipe(
      ofType(ProjectCreationActions.runChecksSuccess),
      map(() => ProjectsActions.loadProjects()),
    ),
  { functional: true },
);

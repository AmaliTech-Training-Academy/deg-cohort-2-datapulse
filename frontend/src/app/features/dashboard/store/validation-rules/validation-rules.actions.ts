import { createAction, props } from '@ngrx/store';
import { ValidationRule } from '../../../../shared/models/dashboard.models';
import { CreateRuleRequest } from '../../models/validation-rule.model';

export const loadRules = createAction(
  '[Validation Rules] Load Rules',
  props<{ datasetId: string }>(),
);
export const loadRulesSuccess = createAction(
  '[Validation Rules] Load Rules Success',
  props<{ rules: ValidationRule[] }>(),
);
export const loadRulesFailure = createAction(
  '[Validation Rules] Load Rules Failure',
  props<{ error: string }>(),
);

export const addRule = createAction(
  '[Validation Rules] Add Rule',
  props<{ datasetId: string; request: CreateRuleRequest }>(),
);
export const addRuleSuccess = createAction(
  '[Validation Rules] Add Rule Success',
  props<{ rule: ValidationRule }>(),
);
export const addRuleFailure = createAction(
  '[Validation Rules] Add Rule Failure',
  props<{ error: string }>(),
);

export const deleteRule = createAction(
  '[Validation Rules] Delete Rule',
  props<{ ruleId: string }>(),
);
export const deleteRuleSuccess = createAction(
  '[Validation Rules] Delete Rule Success',
  props<{ ruleId: string }>(),
);
export const deleteRuleFailure = createAction(
  '[Validation Rules] Delete Rule Failure',
  props<{ error: string }>(),
);

export const runChecksOnDataset = createAction(
  '[Validation Rules] Run Checks On Dataset',
  props<{ datasetId: string }>(),
);
export const runChecksOnDatasetSuccess = createAction(
  '[Validation Rules] Run Checks On Dataset Success',
);
export const runChecksOnDatasetFailure = createAction(
  '[Validation Rules] Run Checks On Dataset Failure',
  props<{ error: string }>(),
);

export const clearValidationRules = createAction('[Validation Rules] Clear');

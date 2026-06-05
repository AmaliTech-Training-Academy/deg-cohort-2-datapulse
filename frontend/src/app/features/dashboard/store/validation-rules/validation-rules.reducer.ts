import { createEntityAdapter, EntityState } from '@ngrx/entity';
import { createReducer, on } from '@ngrx/store';
import { ValidationRule } from '../../../../shared/models/dashboard.models';
import * as ValidationRulesActions from './validation-rules.actions';

export const adapter = createEntityAdapter<ValidationRule>();

export interface ValidationRulesState extends EntityState<ValidationRule> {
  datasetId: string | null;
  loading: boolean;
  error: string | null;
  addLoading: boolean;
  addError: string | null;
  deleteLoadingId: string | null;
  deleteError: string | null;
  runCheckLoading: boolean;
  runCheckError: string | null;
  hasChanges: boolean;
}

const initialState: ValidationRulesState = adapter.getInitialState({
  datasetId: null,
  loading: false,
  error: null,
  addLoading: false,
  addError: null,
  deleteLoadingId: null,
  deleteError: null,
  runCheckLoading: false,
  runCheckError: null,
  hasChanges: false,
});

export const validationRulesReducer = createReducer(
  initialState,
  on(ValidationRulesActions.loadRules, (state, { datasetId }) => ({
    ...state,
    datasetId,
    loading: true,
    error: null,
  })),
  on(ValidationRulesActions.loadRulesSuccess, (state, { rules }) =>
    adapter.setAll(rules, { ...state, loading: false, hasChanges: false }),
  ),
  on(ValidationRulesActions.loadRulesFailure, (state, { error }) => ({
    ...state,
    loading: false,
    error,
  })),

  on(ValidationRulesActions.addRule, (state) => ({
    ...state,
    addLoading: true,
    addError: null,
  })),
  on(ValidationRulesActions.addRuleSuccess, (state, { rule }) =>
    adapter.addOne(rule, { ...state, addLoading: false, hasChanges: true }),
  ),
  on(ValidationRulesActions.addRuleFailure, (state, { error }) => ({
    ...state,
    addLoading: false,
    addError: error,
  })),

  on(ValidationRulesActions.deleteRule, (state, { ruleId }) => ({
    ...state,
    deleteLoadingId: ruleId,
    deleteError: null,
  })),
  on(ValidationRulesActions.deleteRuleSuccess, (state, { ruleId }) =>
    adapter.removeOne(ruleId, { ...state, deleteLoadingId: null, hasChanges: true }),
  ),
  on(ValidationRulesActions.deleteRuleFailure, (state, { error }) => ({
    ...state,
    deleteLoadingId: null,
    deleteError: error,
  })),

  on(ValidationRulesActions.runChecksOnDataset, (state) => ({
    ...state,
    runCheckLoading: true,
    runCheckError: null,
  })),
  on(ValidationRulesActions.runChecksOnDatasetSuccess, (state) => ({
    ...state,
    runCheckLoading: false,
    hasChanges: false,
  })),
  on(ValidationRulesActions.runChecksOnDatasetFailure, (state, { error }) => ({
    ...state,
    runCheckLoading: false,
    runCheckError: error,
  })),

  on(ValidationRulesActions.clearValidationRules, () => initialState),
);

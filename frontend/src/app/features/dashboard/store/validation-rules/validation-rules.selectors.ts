import { createFeatureSelector, createSelector } from '@ngrx/store';
import { adapter, ValidationRulesState } from './validation-rules.reducer';

const selectState = createFeatureSelector<ValidationRulesState>('validationRules');

const { selectAll } = adapter.getSelectors();

export const selectAllRules = createSelector(selectState, selectAll);
export const selectRulesLoading = createSelector(selectState, (s) => s.loading);
export const selectRulesError = createSelector(selectState, (s) => s.error);
export const selectAddRuleLoading = createSelector(selectState, (s) => s.addLoading);
export const selectAddRuleError = createSelector(selectState, (s) => s.addError);
export const selectDeleteLoadingId = createSelector(selectState, (s) => s.deleteLoadingId);
export const selectDeleteError = createSelector(selectState, (s) => s.deleteError);
export const selectRunCheckLoading = createSelector(selectState, (s) => s.runCheckLoading);
export const selectRunCheckError = createSelector(selectState, (s) => s.runCheckError);
export const selectHasChanges = createSelector(selectState, (s) => s.hasChanges);
export const selectValidationRulesDatasetId = createSelector(selectState, (s) => s.datasetId);

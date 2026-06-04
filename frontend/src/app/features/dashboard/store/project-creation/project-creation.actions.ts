import { createAction, props } from '@ngrx/store';
import { SuggestedRule } from '../../../../shared/models/dashboard.models';

export const uploadDataset = createAction(
  '[Project Creation] Upload Dataset',
  props<{ file: File; fileTitle: string; description: string }>(),
);
export const uploadDatasetSuccess = createAction(
  '[Project Creation] Upload Dataset Success',
  props<{ datasetId: string; columns: string[] }>(),
);
export const uploadDatasetFailure = createAction(
  '[Project Creation] Upload Dataset Failure',
  props<{ error: string }>(),
);

export const saveRules = createAction(
  '[Project Creation] Save Rules',
  props<{ rules: SuggestedRule[] }>(),
);
export const saveRulesSuccess = createAction('[Project Creation] Save Rules Success');
export const saveRulesFailure = createAction(
  '[Project Creation] Save Rules Failure',
  props<{ error: string }>(),
);

export const runChecks = createAction('[Project Creation] Run Checks');
export const runChecksSuccess = createAction(
  '[Project Creation] Run Checks Success',
  props<{ score: number }>(),
);
export const runChecksFailure = createAction(
  '[Project Creation] Run Checks Failure',
  props<{ error: string }>(),
);

export const goBackToUpload = createAction('[Project Creation] Go Back To Upload');
export const goBackToRules = createAction('[Project Creation] Go Back To Rules');
export const resetProjectCreation = createAction('[Project Creation] Reset');

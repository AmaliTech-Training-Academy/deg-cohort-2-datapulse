import { createAction, props } from '@ngrx/store';
import { ApiDataset } from '../../models/project.model';

export const loadProjectDetail = createAction(
  '[Project Detail] Load Project Detail',
  props<{ datasetId: string }>(),
);
export const loadProjectDetailSuccess = createAction(
  '[Project Detail] Load Project Detail Success',
  props<{ dataset: ApiDataset }>(),
);
export const loadProjectDetailFailure = createAction(
  '[Project Detail] Load Project Detail Failure',
  props<{ error: string }>(),
);
export const clearProjectDetail = createAction('[Project Detail] Clear');

export const uploadVersion = createAction(
  '[Project Detail] Upload Version',
  props<{ datasetId: string; file: File }>(),
);
export const uploadVersionSuccess = createAction(
  '[Project Detail] Upload Version Success',
  props<{ datasetId: string }>(),
);
export const uploadVersionFailure = createAction(
  '[Project Detail] Upload Version Failure',
  props<{ error: string }>(),
);

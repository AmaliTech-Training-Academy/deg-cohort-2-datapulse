import { createAction, props } from '@ngrx/store';
import { Project } from '../../models/project.model';

export const loadProjects = createAction('[Projects] Load Projects');
export const loadProjectsSuccess = createAction(
  '[Projects] Load Projects Success',
  props<{ projects: Project[] }>(),
);
export const loadProjectsFailure = createAction(
  '[Projects] Load Projects Failure',
  props<{ error: string }>(),
);

export const deleteProject = createAction(
  '[Projects] Delete Project',
  props<{ datasetId: string }>(),
);
export const deleteProjectSuccess = createAction(
  '[Projects] Delete Project Success',
  props<{ datasetId: string }>(),
);
export const deleteProjectFailure = createAction(
  '[Projects] Delete Project Failure',
  props<{ error: string }>(),
);

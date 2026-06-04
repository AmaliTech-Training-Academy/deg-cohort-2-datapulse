import { createReducer, on } from '@ngrx/store';
import { EntityState, EntityAdapter, createEntityAdapter } from '@ngrx/entity';
import { Project } from '../../models/project.model';
import * as ProjectsActions from './projects.actions';

export interface ProjectsState extends EntityState<Project> {
  loading: boolean;
  error: string | null;
}

export const projectAdapter: EntityAdapter<Project> = createEntityAdapter<Project>();

export const initialState: ProjectsState = projectAdapter.getInitialState({
  loading: false,
  error: null,
});

export const projectsReducer = createReducer(
  initialState,
  on(ProjectsActions.loadProjects, (state) => ({ ...state, loading: true, error: null })),
  on(ProjectsActions.loadProjectsSuccess, (state, { projects }) =>
    projectAdapter.setAll(projects, { ...state, loading: false }),
  ),
  on(ProjectsActions.loadProjectsFailure, (state, { error }) => ({
    ...state,
    loading: false,
    error,
  })),
);

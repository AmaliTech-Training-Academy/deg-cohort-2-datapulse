import { inject } from '@angular/core';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { catchError, exhaustMap, map, switchMap } from 'rxjs/operators';
import { of } from 'rxjs';
import * as ProjectsActions from './projects.actions';
import { DashboardApiService } from '../../services/dashboard-api.service';
import { mapDashboardItems } from '../../models/project.model';

export const loadProjectsEffect = createEffect(
  (actions$ = inject(Actions), api = inject(DashboardApiService)) =>
    actions$.pipe(
      ofType(ProjectsActions.loadProjects),
      switchMap(() =>
        api.getProjects().pipe(
          map((response) =>
            ProjectsActions.loadProjectsSuccess({
              projects: mapDashboardItems(response.results),
            }),
          ),
          catchError((err) => of(ProjectsActions.loadProjectsFailure({ error: err.message }))),
        ),
      ),
    ),
  { functional: true },
);

export const deleteProjectEffect = createEffect(
  (actions$ = inject(Actions), api = inject(DashboardApiService)) =>
    actions$.pipe(
      ofType(ProjectsActions.deleteProject),
      exhaustMap(({ datasetId }) =>
        api.deleteDataset(datasetId).pipe(
          map(() => ProjectsActions.deleteProjectSuccess({ datasetId })),
          catchError((err) =>
            of(ProjectsActions.deleteProjectFailure({ error: err.message ?? 'Delete failed.' })),
          ),
        ),
      ),
    ),
  { functional: true },
);

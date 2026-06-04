import { ApplicationConfig, provideBrowserGlobalErrorListeners } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { provideStore } from '@ngrx/store';
import { provideEffects } from '@ngrx/effects';
import { provideStoreDevtools } from '@ngrx/store-devtools';

import { environment } from '../environments/environment';
import { routes } from './app.routes';
import { authReducer } from './features/auth/store/auth.reducer';
import * as authEffects from './features/auth/store/auth.effects';
import { authInterceptor } from './core/interceptors/auth.interceptor';
import { errorInterceptor } from './core/interceptors/error.interceptor';
import { projectsReducer } from './features/dashboard/store/projects/projects.reducer';
import * as projectsEffects from './features/dashboard/store/projects/projects.effects';
import { projectDetailReducer } from './features/dashboard/store/project-detail/project-detail.reducer';
import * as projectDetailEffects from './features/dashboard/store/project-detail/project-detail.effects';
import { reportsReducer } from './features/dashboard/store/reports/reports.reducer';
import * as reportsEffects from './features/dashboard/store/reports/reports.effects';
import { trendsReducer } from './features/dashboard/store/trends/trends.reducer';
import * as trendsEffects from './features/dashboard/store/trends/trends.effects';
import { reportDetailReducer } from './features/dashboard/store/report-detail/report-detail.reducer';
import * as reportDetailEffects from './features/dashboard/store/report-detail/report-detail.effects';

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideRouter(routes),
    // errorInterceptor first so authInterceptor handles the raw HttpErrorResponse (401 refresh logic)
    provideHttpClient(withInterceptors([errorInterceptor, authInterceptor])),
    provideStore({
      auth: authReducer,
      projects: projectsReducer,
      projectDetail: projectDetailReducer,
      reports: reportsReducer,
      trends: trendsReducer,
      reportDetail: reportDetailReducer,
    }),
    provideEffects(
      authEffects,
      projectsEffects,
      projectDetailEffects,
      reportsEffects,
      trendsEffects,
      reportDetailEffects,
    ),
    ...(environment.production ? [] : [provideStoreDevtools({ maxAge: 25 })]),
  ],
};

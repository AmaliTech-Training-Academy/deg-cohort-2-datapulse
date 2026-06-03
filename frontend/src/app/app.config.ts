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
import { mockAuthInterceptor } from './core/interceptors/mock-auth.interceptor';

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideRouter(routes),
    provideHttpClient(
      withInterceptors([
        ...(!environment.production ? [mockAuthInterceptor] : []),
        authInterceptor,
        errorInterceptor,
      ]),
    ),
    provideStore({ auth: authReducer }),
    provideEffects(authEffects),
    ...(environment.production ? [] : [provideStoreDevtools({ maxAge: 25 })]),
  ],
};

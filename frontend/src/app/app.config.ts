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

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideRouter(routes),
    // errorInterceptor first so authInterceptor handles the raw HttpErrorResponse (401 refresh logic)
    provideHttpClient(withInterceptors([errorInterceptor, authInterceptor])),
    provideStore({ auth: authReducer }),
    provideEffects(authEffects),
    ...(environment.production ? [] : [provideStoreDevtools({ maxAge: 25 })]),
  ],
};

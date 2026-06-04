import { createFeatureSelector, createSelector } from '@ngrx/store';
import { AuthState } from '../auth.models';

export const selectAuthState = createFeatureSelector<AuthState>('auth');

export const selectUser = createSelector(selectAuthState, (state) => state.user);
export const selectAuthLoading = createSelector(selectAuthState, (state) => state.loading);
export const selectAuthError = createSelector(selectAuthState, (state) => state.error);
export const selectIsAuthenticated = createSelector(
  selectAuthState,
  (state) => state.user !== null,
);
export const selectForgotPasswordSent = createSelector(
  selectAuthState,
  (state) => state.forgotPasswordSent,
);
export const selectRegistrationComplete = createSelector(
  selectAuthState,
  (state) => state.registrationComplete,
);
export const selectEmailVerificationSent = createSelector(
  selectAuthState,
  (state) => state.emailVerificationSent,
);
export const selectEmailVerified = createSelector(
  selectAuthState,
  (state) => state.emailVerified,
);
export const selectPasswordResetSuccess = createSelector(
  selectAuthState,
  (state) => state.passwordResetSuccess,
);

export const selectUserRole = createSelector(selectAuthState, (state) => state.user?.role ?? null);

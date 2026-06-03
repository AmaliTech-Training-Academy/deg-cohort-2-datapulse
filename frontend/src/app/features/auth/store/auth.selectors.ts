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

export const selectUserRole = createSelector(selectAuthState, (state) => state.user?.role ?? null);

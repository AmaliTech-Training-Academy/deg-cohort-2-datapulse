import { createFeatureSelector, createSelector } from '@ngrx/store';
import { AdminUsersState } from './admin-users.reducer';

const selectState = createFeatureSelector<AdminUsersState>('adminUsers');

export const selectAdminUsers = createSelector(selectState, (s) => s.users);
export const selectAdminUsersTotal = createSelector(selectState, (s) => s.total);
export const selectAdminUsersLoading = createSelector(selectState, (s) => s.loading);
export const selectAdminUsersError = createSelector(selectState, (s) => s.error);

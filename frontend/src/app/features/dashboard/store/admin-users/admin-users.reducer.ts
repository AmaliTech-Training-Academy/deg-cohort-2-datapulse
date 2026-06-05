import { createReducer, on } from '@ngrx/store';
import { AdminUser } from '../../models/admin-user.model';
import * as AdminUsersActions from './admin-users.actions';

export interface AdminUsersState {
  users: AdminUser[];
  total: number;
  loading: boolean;
  error: string | null;
}

const initialState: AdminUsersState = {
  users: [],
  total: 0,
  loading: false,
  error: null,
};

export const adminUsersReducer = createReducer(
  initialState,
  on(AdminUsersActions.loadAdminUsers, (state) => ({ ...state, loading: true, error: null })),
  on(AdminUsersActions.loadAdminUsersSuccess, (state, { users, total }) => ({
    ...state,
    users,
    total,
    loading: false,
  })),
  on(AdminUsersActions.loadAdminUsersFailure, (state, { error }) => ({
    ...state,
    loading: false,
    error,
  })),
  on(AdminUsersActions.clearAdminUsers, () => initialState),
);

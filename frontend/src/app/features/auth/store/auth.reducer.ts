import { createReducer, on } from '@ngrx/store';
import { AuthState } from '../auth.models';
import * as AuthActions from './auth.actions';

const initialState: AuthState = {
  user: null,
  loading: false,
  error: null,
};

export const authReducer = createReducer(
  initialState,
  on(AuthActions.login, AuthActions.register, (state) => ({ ...state, loading: true, error: null })),
  on(AuthActions.loginSuccess, AuthActions.registerSuccess, (state, { user }) => ({
    ...state,
    user,
    loading: false,
  })),
  on(AuthActions.loginFailure, AuthActions.registerFailure, (state, { error }) => ({
    ...state,
    loading: false,
    error,
  })),
  on(AuthActions.logout, () => initialState),
);

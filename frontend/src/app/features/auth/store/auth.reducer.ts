import { createReducer, on } from '@ngrx/store';
import { AuthState } from '../auth.models';
import * as AuthActions from './auth.actions';

const initialState: AuthState = {
  user: null,
  loading: false,
  error: null,
  forgotPasswordSent: false,
};

export const authReducer = createReducer(
  initialState,
  on(AuthActions.login, AuthActions.register, (state) => ({
    ...state,
    loading: true,
    error: null,
    forgotPasswordSent: false,
  })),
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
  on(AuthActions.forgotPassword, (state) => ({
    ...state,
    loading: true,
    error: null,
    forgotPasswordSent: false,
  })),
  on(AuthActions.forgotPasswordSuccess, (state) => ({
    ...state,
    loading: false,
    forgotPasswordSent: true,
  })),
  on(AuthActions.forgotPasswordFailure, (state, { error }) => ({
    ...state,
    loading: false,
    error,
  })),
  on(AuthActions.logout, () => initialState),
  on(AuthActions.restoreSession, (state, { user }) => ({ ...state, user })),
  on(AuthActions.restoreSessionEmpty, (state) => state),
);

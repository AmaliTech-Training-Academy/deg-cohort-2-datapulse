import { createReducer, on } from '@ngrx/store';
import { AuthState } from '../auth.models';
import * as AuthActions from './auth.actions';

const initialState: AuthState = {
  user: null,
  loading: false,
  error: null,
  forgotPasswordSent: false,
  registrationComplete: false,
  emailVerificationSent: false,
  emailVerified: false,
  passwordResetSuccess: false,
};

export const authReducer = createReducer(
  initialState,

  // Login
  on(AuthActions.login, (state) => ({
    ...state,
    loading: true,
    error: null,
  })),
  on(AuthActions.loginSuccess, (state, { user }) => ({
    ...state,
    user,
    loading: false,
  })),
  on(AuthActions.loginFailure, (state, { error }) => ({
    ...state,
    loading: false,
    error,
  })),

  // Register
  on(AuthActions.register, (state) => ({
    ...state,
    loading: true,
    error: null,
    registrationComplete: false,
  })),
  on(AuthActions.registerSuccess, (state) => ({
    ...state,
    loading: false,
    registrationComplete: true,
  })),
  on(AuthActions.registerFailure, (state, { error }) => ({
    ...state,
    loading: false,
    error,
  })),

  // Forgot password
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

  // Resend verification
  on(AuthActions.resendVerification, (state) => ({
    ...state,
    loading: true,
    error: null,
    emailVerificationSent: false,
  })),
  on(AuthActions.resendVerificationSuccess, (state) => ({
    ...state,
    loading: false,
    emailVerificationSent: true,
  })),
  on(AuthActions.resendVerificationFailure, (state, { error }) => ({
    ...state,
    loading: false,
    error,
  })),

  // Verify email
  on(AuthActions.verifyEmail, (state) => ({
    ...state,
    loading: true,
    error: null,
    emailVerified: false,
  })),
  on(AuthActions.verifyEmailSuccess, (state) => ({
    ...state,
    loading: false,
    emailVerified: true,
  })),
  on(AuthActions.verifyEmailFailure, (state, { error }) => ({
    ...state,
    loading: false,
    error,
  })),

  // Reset password
  on(AuthActions.resetPassword, (state) => ({
    ...state,
    loading: true,
    error: null,
    passwordResetSuccess: false,
  })),
  on(AuthActions.resetPasswordSuccess, (state) => ({
    ...state,
    loading: false,
    passwordResetSuccess: true,
  })),
  on(AuthActions.resetPasswordFailure, (state, { error }) => ({
    ...state,
    loading: false,
    error,
  })),

  on(AuthActions.logout, () => initialState),
  on(AuthActions.restoreSession, (state, { user }) => ({ ...state, user })),
  on(AuthActions.restoreSessionEmpty, (state) => state),
);

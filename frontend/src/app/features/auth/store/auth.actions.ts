import { createAction, props } from '@ngrx/store';
import {
  ForgotPasswordCredentials,
  LoginCredentials,
  RegisterCredentials,
  ResetPasswordCredentials,
  User,
} from '../auth.models';

export const login = createAction('[Auth] Login', props<LoginCredentials>());
export const loginSuccess = createAction(
  '[Auth] Login Success',
  props<{ user: User; access: string; refresh: string }>(),
);
export const loginFailure = createAction('[Auth] Login Failure', props<{ error: string }>());

export const register = createAction('[Auth] Register', props<RegisterCredentials>());
export const registerSuccess = createAction('[Auth] Register Success', props<{ user: User }>());
export const registerFailure = createAction('[Auth] Register Failure', props<{ error: string }>());

export const forgotPassword = createAction(
  '[Auth] Forgot Password',
  props<ForgotPasswordCredentials>(),
);
export const forgotPasswordSuccess = createAction('[Auth] Forgot Password Success');
export const forgotPasswordFailure = createAction(
  '[Auth] Forgot Password Failure',
  props<{ error: string }>(),
);

export const resendVerification = createAction(
  '[Auth] Resend Verification',
  props<{ email: string }>(),
);
export const resendVerificationSuccess = createAction('[Auth] Resend Verification Success');
export const resendVerificationFailure = createAction(
  '[Auth] Resend Verification Failure',
  props<{ error: string }>(),
);

export const verifyEmail = createAction('[Auth] Verify Email', props<{ token: string }>());
export const verifyEmailSuccess = createAction('[Auth] Verify Email Success');
export const verifyEmailFailure = createAction(
  '[Auth] Verify Email Failure',
  props<{ error: string }>(),
);

export const resetPassword = createAction(
  '[Auth] Reset Password',
  props<ResetPasswordCredentials>(),
);
export const resetPasswordSuccess = createAction('[Auth] Reset Password Success');
export const resetPasswordFailure = createAction(
  '[Auth] Reset Password Failure',
  props<{ error: string }>(),
);

export const logout = createAction('[Auth] Logout');

export const restoreSession = createAction('[Auth] Restore Session', props<{ user: User }>());
export const restoreSessionEmpty = createAction('[Auth] Restore Session Empty');

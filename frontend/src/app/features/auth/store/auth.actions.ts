import { createAction, props } from '@ngrx/store';
import { LoginCredentials, RegisterCredentials, ForgotPasswordCredentials, User } from '../auth.models';

export const login = createAction('[Auth] Login', props<LoginCredentials>());
export const loginSuccess = createAction('[Auth] Login Success', props<{ user: User; token: string }>());
export const loginFailure = createAction('[Auth] Login Failure', props<{ error: string }>());

export const register = createAction('[Auth] Register', props<RegisterCredentials>());
export const registerSuccess = createAction('[Auth] Register Success', props<{ user: User; token: string }>());
export const registerFailure = createAction('[Auth] Register Failure', props<{ error: string }>());

export const forgotPassword = createAction('[Auth] Forgot Password', props<ForgotPasswordCredentials>());
export const forgotPasswordSuccess = createAction('[Auth] Forgot Password Success');
export const forgotPasswordFailure = createAction('[Auth] Forgot Password Failure', props<{ error: string }>());

export const logout = createAction('[Auth] Logout');

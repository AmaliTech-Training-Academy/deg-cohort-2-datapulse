export type UserRole = 'admin' | 'user';

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: UserRole;
  created_at: string;
  is_email_verified: boolean;
}

export interface AuthState {
  user: User | null;
  loading: boolean;
  error: string | null;
  forgotPasswordSent: boolean;
  registrationComplete: boolean;
  emailVerificationSent: boolean;
  emailVerified: boolean;
  passwordResetSuccess: boolean;
}

export const ACCESS_TOKEN_KEY = 'auth_access_token';
export const REFRESH_TOKEN_KEY = 'auth_refresh_token';
export const AUTH_USER_KEY = 'auth_user';

// Request payloads
export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterCredentials {
  email: string;
  first_name: string;
  last_name: string;
  password: string;
}

export interface ForgotPasswordCredentials {
  email: string;
}

export interface ResendVerificationCredentials {
  email: string;
}

export interface VerifyEmailCredentials {
  token: string;
}

export interface ResetPasswordCredentials {
  uid: string;
  token: string;
  password: string;
}

// API response shapes
export interface LoginResponse {
  access: string;
  refresh: string;
  user: User;
}

export interface RefreshResponse {
  access: string;
  refresh: string;
}

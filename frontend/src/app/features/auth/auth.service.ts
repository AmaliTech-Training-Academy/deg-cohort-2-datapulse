import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { LoginResponse, RefreshResponse, User } from './auth.models';
import { environment } from '../../../environments/environment';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${environment.apiUrl}/v1/auth`;

  login(email: string, password: string): Observable<LoginResponse> {
    return this.http.post<LoginResponse>(`${this.baseUrl}/login/`, { email, password });
  }

  register(
    email: string,
    first_name: string,
    last_name: string,
    password: string,
  ): Observable<User> {
    return this.http.post<User>(`${this.baseUrl}/register/`, {
      email,
      first_name,
      last_name,
      password,
    });
  }

  me(): Observable<User> {
    return this.http.get<User>(`${this.baseUrl}/me/`);
  }

  refresh(refreshToken: string): Observable<RefreshResponse> {
    return this.http.post<RefreshResponse>(`${this.baseUrl}/refresh/`, { refresh: refreshToken });
  }

  forgotPassword(email: string): Observable<void> {
    return this.http.post<void>(`${this.baseUrl}/forgot-password/`, { email });
  }

  resendVerification(email: string): Observable<void> {
    return this.http.post<void>(`${this.baseUrl}/resend-verification/`, { email });
  }

  verifyEmail(token: string): Observable<void> {
    return this.http.post<void>(`${this.baseUrl}/verify-email/`, { token });
  }

  resetPassword(uid: string, token: string, password: string): Observable<void> {
    return this.http.post<void>(`${this.baseUrl}/reset-password/`, { uid, token, password });
  }
}

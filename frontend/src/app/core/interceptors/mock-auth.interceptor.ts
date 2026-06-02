import { HttpErrorResponse, HttpInterceptorFn, HttpResponse } from '@angular/common/http';
import { throwError, of } from 'rxjs';
import { User, UserRole } from '../../features/auth/auth.models';

interface MockCredential {
  email: string;
  password: string;
  user: User;
}

const MOCK_CREDENTIALS: MockCredential[] = [
  {
    email: 'admin@datapulse.io',
    password: 'admin123',
    user: {
      id: 'u1',
      name: 'Ava Chen',
      email: 'admin@datapulse.io',
      role: 'admin' as UserRole,
    },
  },
  {
    email: 'user@datapulse.io',
    password: 'user123',
    user: {
      id: 'u2',
      name: 'Jordan Lee',
      email: 'user@datapulse.io',
      role: 'user' as UserRole,
    },
  },
];

export const mockAuthInterceptor: HttpInterceptorFn = (req, next) => {
  if (!req.url.includes('/auth/')) {
    return next(req);
  }

  if (req.url.endsWith('/auth/login')) {
    const body = req.body as { email: string; password: string };
    const match = MOCK_CREDENTIALS.find(
      (c) => c.email === body?.email && c.password === body?.password,
    );
    if (!match) {
      return throwError(
        () =>
          new HttpErrorResponse({
            status: 401,
            error: { message: 'Invalid email or password' },
          }),
      );
    }
    return of(
      new HttpResponse({
        status: 200,
        body: { user: match.user, token: `mock-token-${match.user.id}` },
      }),
    );
  }

  if (req.url.endsWith('/auth/register')) {
    const body = req.body as { name: string; email: string; password: string };
    const newUser: User = {
      id: `u-${Date.now()}`,
      name: body?.name ?? 'New User',
      email: body?.email ?? '',
      role: 'user',
    };
    return of(
      new HttpResponse({
        status: 201,
        body: { user: newUser, token: `mock-token-${newUser.id}` },
      }),
    );
  }

  if (req.url.endsWith('/auth/logout')) {
    return of(new HttpResponse({ status: 200, body: {} }));
  }

  if (req.url.includes('/auth/forgot-password') || req.url.includes('/auth/reset-password')) {
    return of(new HttpResponse({ status: 200, body: {} }));
  }

  return next(req);
};

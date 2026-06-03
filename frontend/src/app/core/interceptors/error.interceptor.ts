import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';

function extractMessage(err: HttpErrorResponse): string {
  const b = err.error;
  if (!b || typeof b === 'string') return err.message;
  if (b.message) return b.message;
  if (b.detail) return b.detail;
  // Validation error: pick the first field's first message
  const firstKey = Object.keys(b)[0];
  if (firstKey) {
    const val = b[firstKey];
    return Array.isArray(val) ? val[0] : String(val);
  }
  return err.message;
}

export const errorInterceptor: HttpInterceptorFn = (req, next) =>
  next(req).pipe(
    catchError((err: HttpErrorResponse) => throwError(() => new Error(extractMessage(err)))),
  );

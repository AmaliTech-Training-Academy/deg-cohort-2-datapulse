import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';

function extractMessage(err: HttpErrorResponse): string {
  const b = err.error;
  if (!b || typeof b === 'string') return err.message;
  // Handle { error: { code, message, fields } } envelope shape
  if (b.error && typeof b.error === 'object') {
    const inner = b.error;
    if (inner.message) return inner.message;
    if (inner.fields && typeof inner.fields === 'object') {
      const firstField = Object.keys(inner.fields)[0];
      if (firstField) return String(inner.fields[firstField]);
    }
  }
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

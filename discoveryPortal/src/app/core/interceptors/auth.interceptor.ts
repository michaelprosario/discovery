import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, switchMap, throwError } from 'rxjs';
import { AuthService } from '../services/auth.service';

/**
 * HTTP Interceptor to add Firebase ID token to all API requests
 */
export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  // Skip authentication for login/signup requests and Firebase URLs
  if (req.url.includes('/auth/') || req.url.includes('firebaseapp.com') || req.url.includes('googleapis.com')) {
    return next(req);
  }

  // Get ID token and add to request
  return authService.getIdToken().pipe(
    switchMap(token => {
      // Clone request and add authorization header if token exists
      const authReq = token
        ? req.clone({
            setHeaders: {
              Authorization: `Bearer ${token}`
            }
          })
        : req;

      // Send the request
      return next(authReq).pipe(
        catchError((error: HttpErrorResponse) => {
          // Handle authentication errors
          if (error.status === 401) {
            // Token expired or invalid - logout and redirect to login
            authService.logout().subscribe(() => {
              router.navigate(['/login'], {
                queryParams: { returnUrl: router.url }
              });
            });
          }

          if (error.status === 403) {
            // Forbidden - user doesn't have permission
            console.error('Access forbidden:', error);
            // Optionally redirect to a "no permission" page
          }

          return throwError(() => error);
        })
      );
    })
  );
};

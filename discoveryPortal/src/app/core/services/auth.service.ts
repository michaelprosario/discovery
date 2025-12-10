import { Injectable, inject, signal, computed } from '@angular/core';
import { Observable, from, of, throwError } from 'rxjs';
import { map, catchError, tap, switchMap } from 'rxjs/operators';
import { 
  Auth, 
  signInWithEmailAndPassword, 
  signOut, 
  createUserWithEmailAndPassword,
  User,
  user,
  UserCredential,
  AuthError,
  updateProfile,
  GoogleAuthProvider,
  signInWithPopup
} from '@angular/fire/auth';

export interface AuthUser {
  uid: string;
  email: string;
  displayName: string | null;
  photoURL: string | null;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface SignupCredentials extends LoginCredentials {
  displayName?: string;
}

export interface AuthState {
  user: AuthUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private auth = inject(Auth);
  
  // Signals for reactive state management
  private authState = signal<AuthState>({
    user: null,
    isAuthenticated: false,
    isLoading: true,
    error: null
  });

  // Public computed signals
  readonly user = computed(() => this.authState().user);
  readonly isAuthenticated = computed(() => this.authState().isAuthenticated);
  readonly isLoading = computed(() => this.authState().isLoading);
  readonly error = computed(() => this.authState().error);

  // Observable for async pipe compatibility
  readonly user$ = user(this.auth).pipe(
    map((firebaseUser: User | null) => {
      if (!firebaseUser) return null;
      return {
        uid: firebaseUser.uid,
        email: firebaseUser.email!,
        displayName: firebaseUser.displayName,
        photoURL: firebaseUser.photoURL
      } as AuthUser;
    })
  );

  constructor() {
    this.initializeAuthListener();
  }

  /**
   * Initialize Firebase auth state listener
   */
  private initializeAuthListener(): void {
    user(this.auth).subscribe({
      next: (firebaseUser: User | null) => {
        if (firebaseUser) {
          const authUser: AuthUser = {
            uid: firebaseUser.uid,
            email: firebaseUser.email!,
            displayName: firebaseUser.displayName,
            photoURL: firebaseUser.photoURL
          };
          
          this.authState.update(state => ({
            ...state,
            user: authUser,
            isAuthenticated: true,
            isLoading: false,
            error: null
          }));
        } else {
          this.authState.update(state => ({
            ...state,
            user: null,
            isAuthenticated: false,
            isLoading: false,
            error: null
          }));
        }
      },
      error: (error: AuthError) => {
        console.error('Auth state error:', error);
        this.authState.update(state => ({
          ...state,
          user: null,
          isAuthenticated: false,
          isLoading: false,
          error: error.message
        }));
      }
    });
  }

  /**
   * Sign in with email and password
   */
  login(credentials: LoginCredentials): Observable<UserCredential> {
    this.authState.update(state => ({ ...state, isLoading: true, error: null }));
    
    return from(
      signInWithEmailAndPassword(this.auth, credentials.email, credentials.password)
    ).pipe(
      tap(() => {
        this.authState.update(state => ({ ...state, isLoading: false }));
      }),
      catchError((error: AuthError) => {
        const errorMessage = this.getErrorMessage(error);
        this.authState.update(state => ({
          ...state,
          isLoading: false,
          error: errorMessage
        }));
        return throwError(() => new Error(errorMessage));
      })
    );
  }

  /**
   * Sign in with Google
   */
  loginWithGoogle(): Observable<UserCredential> {
    this.authState.update(state => ({ ...state, isLoading: true, error: null }));
    
    const provider = new GoogleAuthProvider();
    // Optional: Add scopes if needed
    // provider.addScope('https://www.googleapis.com/auth/userinfo.email');
    
    return from(signInWithPopup(this.auth, provider)).pipe(
      tap(() => {
        this.authState.update(state => ({ ...state, isLoading: false }));
      }),
      catchError((error: AuthError) => {
        const errorMessage = this.getErrorMessage(error);
        this.authState.update(state => ({
          ...state,
          isLoading: false,
          error: errorMessage
        }));
        return throwError(() => new Error(errorMessage));
      })
    );
  }

  /**
   * Create new user account
   */
  signup(credentials: SignupCredentials): Observable<UserCredential> {
    this.authState.update(state => ({ ...state, isLoading: true, error: null }));
    
    return from(
      createUserWithEmailAndPassword(this.auth, credentials.email, credentials.password)
    ).pipe(
      switchMap((userCredential) => {
        // Update profile with display name if provided
        if (credentials.displayName && userCredential.user) {
          return from(
            updateProfile(userCredential.user, { displayName: credentials.displayName })
          ).pipe(map(() => userCredential));
        }
        return of(userCredential);
      }),
      tap(() => {
        this.authState.update(state => ({ ...state, isLoading: false }));
      }),
      catchError((error: AuthError) => {
        const errorMessage = this.getErrorMessage(error);
        this.authState.update(state => ({
          ...state,
          isLoading: false,
          error: errorMessage
        }));
        return throwError(() => new Error(errorMessage));
      })
    );
  }

  /**
   * Sign out current user
   */
  logout(): Observable<void> {
    return from(signOut(this.auth)).pipe(
      tap(() => {
        this.authState.update(state => ({
          ...state,
          user: null,
          isAuthenticated: false,
          error: null
        }));
      }),
      catchError((error: AuthError) => {
        console.error('Logout error:', error);
        return throwError(() => error);
      })
    );
  }

  /**
   * Get current user's ID token (for API authentication)
   */
  getIdToken(): Observable<string | null> {
    const currentUser = this.auth.currentUser;
    
    if (!currentUser) {
      return of(null);
    }

    return from(currentUser.getIdToken()).pipe(
      catchError((error: AuthError) => {
        console.error('Error getting ID token:', error);
        return of(null);
      })
    );
  }

  /**
   * Force refresh the ID token
   */
  refreshToken(): Observable<string | null> {
    const currentUser = this.auth.currentUser;
    
    if (!currentUser) {
      return of(null);
    }

    return from(currentUser.getIdToken(true)).pipe(
      catchError((error: AuthError) => {
        console.error('Error refreshing token:', error);
        return of(null);
      })
    );
  }

  /**
   * Clear error state
   */
  clearError(): void {
    this.authState.update(state => ({ ...state, error: null }));
  }

  /**
   * Convert Firebase auth errors to user-friendly messages
   */
  private getErrorMessage(error: AuthError): string {
    switch (error.code) {
      case 'auth/invalid-email':
        return 'Invalid email address format.';
      case 'auth/user-disabled':
        return 'This account has been disabled.';
      case 'auth/user-not-found':
        return 'No account found with this email.';
      case 'auth/wrong-password':
        return 'Incorrect password.';
      case 'auth/email-already-in-use':
        return 'An account already exists with this email.';
      case 'auth/weak-password':
        return 'Password should be at least 6 characters.';
      case 'auth/operation-not-allowed':
        return 'Email/password accounts are not enabled.';
      case 'auth/too-many-requests':
        return 'Too many failed attempts. Please try again later.';
      case 'auth/network-request-failed':
        return 'Network error. Please check your connection.';
      case 'auth/invalid-credential':
        return 'Invalid email or password.';
      case 'auth/popup-closed-by-user':
        return 'Sign-in popup was closed before completing.';
      case 'auth/cancelled-popup-request':
        return 'Only one popup request is allowed at a time.';
      case 'auth/popup-blocked':
        return 'Sign-in popup was blocked by the browser.';
      case 'auth/account-exists-with-different-credential':
        return 'An account already exists with the same email but different sign-in credentials.';
      default:
        return error.message || 'An authentication error occurred.';
    }
  }
}

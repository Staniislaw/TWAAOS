import { Inject, Injectable, PLATFORM_ID } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { Observable } from 'rxjs';
import { isPlatformBrowser } from '@angular/common';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private apiUrl = 'http://localhost:8000';
  private isBrowser: boolean;

  constructor(
    private http: HttpClient,
    private router: Router,
    @Inject(PLATFORM_ID) platformId: Object
  ) {
    this.isBrowser = isPlatformBrowser(platformId);
  }

  loginWithGoogle(): void {
    if (this.isBrowser) {
      window.location.href = `${this.apiUrl}/auth/google`;
    }
  }

  googleCallback(code: string): Observable<any> {
    return this.http.get(`${this.apiUrl}/auth/callback?code=${code}`);
  }

  saveToken(token: string): void {
    if (this.isBrowser) {
      localStorage.setItem('access_token', token);
    }
  }

  getToken(): string | null {
    if (this.isBrowser) {
      return localStorage.getItem('access_token');
    }
    return null;
  }
  getUserRole(): string | null {
    const token = localStorage.getItem('access_token');

    if (!token) return null;

    const payload = JSON.parse(atob(token.split('.')[1]));
    return payload.role;
  }

  isLoggedIn(): boolean {
    return !!this.getToken();
  }

  getUser(): any {
    if (this.isBrowser) {
      const user = localStorage.getItem('user');
      return user ? JSON.parse(user) : null;
    }
    return null;
  }

  logout(): void {
    if (this.isBrowser) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
    }
    this.router.navigate(['/login']);
  }
  login(username: string, password: string) {
    return this.http.post<{ access_token: string }>(
        `${this.apiUrl}/auth/login`,
        { username, password }
    );
  }

  register(username: string, password: string) {
    return this.http.post(`${this.apiUrl}/auth/register`, {
      username,
      password
    });
  }
}

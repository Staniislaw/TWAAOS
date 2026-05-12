// guards/admin.guard.ts
import { Injectable } from '@angular/core';
import { CanActivate, Router } from '@angular/router';

@Injectable({ providedIn: 'root' })
export class AdminGuard implements CanActivate {
  constructor(private router: Router) {}

  canActivate(): boolean {
    try {
      const token = localStorage.getItem('access_token')!;
      const payload = JSON.parse(atob(token.split('.')[1]));
      if (payload.role === 'admin') return true;
    } catch {}
    this.router.navigate(['/events']);
    return false;
  }
}
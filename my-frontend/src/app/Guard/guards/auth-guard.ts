import { Injectable } from '@angular/core';
import { CanActivate, ActivatedRouteSnapshot, Router } from '@angular/router';

@Injectable({
  providedIn: 'root'
})
export class AuthGuard implements CanActivate {

  constructor(private router: Router) {}

  canActivate(route: ActivatedRouteSnapshot): boolean {
    const token = localStorage.getItem('access_token');

    if (!token) {
      this.router.navigate(['/login']);
      return false;
    }

    const payload = JSON.parse(atob(token.split('.')[1]));
    const userRole = payload.role;

    const allowedRoles = route.data['roles'];

    if (allowedRoles && !allowedRoles.includes(userRole)) {
      this.router.navigate(['/events']);
      return false;
    }

    return true;
  }
}
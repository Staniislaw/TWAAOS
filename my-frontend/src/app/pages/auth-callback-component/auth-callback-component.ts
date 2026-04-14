import { Component, Inject, OnInit, PLATFORM_ID } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { CommonModule, isPlatformBrowser } from '@angular/common';
import { AuthService } from '../../services/auth';

@Component({
  selector: 'app-auth-callback-component',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './auth-callback-component.html',
  styleUrl: './auth-callback-component.css',
})
export class AuthCallbackComponent implements OnInit {
  message = 'Se procesează autentificarea...';
  private isBrowser: boolean;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private authService: AuthService,
    @Inject(PLATFORM_ID) platformId: Object
  ) {
    this.isBrowser = isPlatformBrowser(platformId);
  }

  ngOnInit(): void {
    if (!this.isBrowser) return;

    const token = this.route.snapshot.queryParamMap.get('token');
    const name = this.route.snapshot.queryParamMap.get('name');
    const email = this.route.snapshot.queryParamMap.get('email');

    if (token) {
      this.authService.saveToken(token);
      localStorage.setItem('user', JSON.stringify({ name, email }));

      this.message = 'Autentificare reușită! Redirecționare...';
      setTimeout(() => this.router.navigate(['/events']), 1000);
    } else {
      setTimeout(() => this.router.navigate(['/login']), 2000);
    }
  }
}


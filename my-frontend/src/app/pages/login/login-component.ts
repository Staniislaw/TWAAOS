import { Component } from '@angular/core';
import { AuthService } from '../../services/auth';
import { Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-login',
  imports: [FormsModule, CommonModule],
  templateUrl: './login-component.html',
  styleUrl: './login-component.css',
})
export class LoginComponent {
  username = '';
  password = '';
  errorMessage = '';
  isLoading = false;
  activeTab = 'signin';


  constructor(private authService: AuthService, private router: Router) {}

  login(): void {
    if (!this.username || !this.password) {
      this.errorMessage = 'Completeaza toate campurile!';
      return;
    }

    this.isLoading = true;
    this.authService.login(this.username, this.password).subscribe({
      next: (response) => {
        if (response.access_token) {
          this.authService.saveToken(response.access_token);
          this.router.navigate(['/events']);
        } else {
          this.errorMessage = 'Credentiale incorecte!';
        }
        this.isLoading = false;
      },
      error: () => {
        this.errorMessage = 'Eroare la conectare!';
        this.isLoading = false;
      }
    });
  }

  loginWithGoogle(): void {
    this.authService.loginWithGoogle();
  }
}

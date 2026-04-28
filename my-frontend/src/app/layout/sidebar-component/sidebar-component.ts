import { Component } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { CommonModule } from '@angular/common';


@Component({
  selector: 'app-sidebar-component',
  standalone: true,
  imports: [CommonModule, RouterLink, RouterLinkActive],
  templateUrl: './sidebar-component.html',
  styleUrl: './sidebar-component.css',
})
export class SidebarComponent {
  userRole: string | null = null;

  navItems = [
    { label: 'Evenimente', icon: '📅', route: '/events' },
    { label: 'Home', icon: '🏠', route: '/home' },
    { label: 'Înregistrările mele', icon: '📋', route: '/my-registrations' },
    { label: 'Materiale', icon: '📁', route: '/materials' },
    { label: 'Feedback', icon: '⭐', route: '/feedback' },
  ]; 

  footerItems = [
    { label: 'Setări', icon: '⚙️', route: '/settings' },
    { label: 'Deconectare', icon: '🚪', route: '/login' },
  ];
  ngOnInit() {
    const token = localStorage.getItem('access_token'); 
    if (token) {
      const payload = JSON.parse(atob(token.split('.')[1]));
      this.userRole = payload.role;
    }
  }
}
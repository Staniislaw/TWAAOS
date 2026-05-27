import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { SidebarComponent } from '../../layout/sidebar-component/sidebar-component';
import { EventService } from '../../services/event-service';
import { MatIconModule } from '@angular/material/icon';

@Component({
  selector: 'app-my-registrations',
  imports: [CommonModule, SidebarComponent, MatIconModule],
  templateUrl: './my-registrations.html',
  styleUrl: './my-registrations.css',
})
export class MyRegistrations implements OnInit {
  registrations: any[] = [];
  isLoading = true;
  errorMessage = '';

  constructor(
    private router: Router,
    private eventService: EventService
  ) {}

  ngOnInit(): void {
    this.eventService.getMyRegistrations().subscribe({
      next: (data) => {
        this.registrations = data;
        this.isLoading = false;
      },
      error: () => {
        this.errorMessage = 'Nu s-au putut încărca înregistrările!';
        this.isLoading = false;
      }
    });
  }

  goToEvent(id: number): void {
    this.router.navigate(['/events', id]);
  }

  unregister(eventId: number, event: MouseEvent): void {
    event.stopPropagation();
    this.eventService.unregisterFromEvent(eventId).subscribe({
      next: () => {
        this.registrations = this.registrations.filter(r => r.id !== eventId);
      },
      error: () => alert('Eroare la dezînscriere!')
    });
  }

  formatDate(dateStr: string): string {
    if (!dateStr) return '—';
    return new Date(dateStr).toLocaleDateString('ro-RO', {
      day: 'numeric', month: 'long', year: 'numeric',
      hour: '2-digit', minute: '2-digit'
    });
  }

  getStatusLabel(status: string): string {
    const map: any = {
      'registered': 'Înscris',
      'waitlist': 'Listă de așteptare',
      'attended': 'Participat'
    };
    return map[status] || status;
  }

  getStatusClass(status: string): string {
    const map: any = {
      'registered': 'status-registered',
      'waitlist': 'status-waitlist',
      'attended': 'status-attended'
    };
    return map[status] || '';
  }

  getCoverColor(category: string): string {
    const map: any = {
      'Technology': '#667eea, #764ba2',
      'Science':    '#11998e, #38ef7d',
      'Design':     '#f093fb, #f5576c',
      'Academic':   '#4facfe, #00f2fe',
      'Research':   '#43e97b, #38f9d7',
      'Arts':       '#fa709a, #fee140'
    };
    return map[category] || '#667eea, #764ba2';
  }
}

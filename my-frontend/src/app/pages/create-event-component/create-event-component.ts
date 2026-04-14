import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Event } from '../../models/event.model';
import { SidebarComponent } from '../../layout/sidebar-component/sidebar-component';
import { EventService } from '../../services/event-service';

@Component({
  selector: 'app-create-event-component',
  standalone: true,
  imports: [CommonModule, FormsModule, SidebarComponent],
  templateUrl: './create-event-component.html',
  styleUrl: './create-event-component.css',
})
export class CreateEventComponent {
  entryTypes = [
    { value: 'free',         label: 'Liber' },
    { value: 'registration', label: 'Înscriere' },
    { value: 'qr_code',      label: 'QR Code' },
  ];

  eventForm: Partial<Event> = {
    title: '',
    description: '',
    category: '',
    faculty: '',
    start_datetime: '',
    end_datetime: '',
    registration_deadline: '',
    location: '',
    participation_mode: 'In-Person',
    entry_type: 'free',
    max_participants: undefined,
    status: 'active'
  };

  isSaving = false;
  isPublishing = false;
  savedMessage = '';
  errorMessage = '';
  activeMode = 'In-Person';
  unlimitedAttendees = false;

  uploadedFiles = [
    { name: 'Syllabus.pdf', size: '1.2 MB', type: 'pdf' }
  ];

  sponsors = [
    { name: 'Microsoft Romania', website: 'microsoft.com' },
    { name: 'Google Romania', website: 'google.com' }
  ];

  categories = ['Conference', 'Workshop', 'Seminar', 'Hackathon', 'Guest Lecture', 'Symposium'];
  faculties = ['FIESC', 'FSE', 'FSEAP', 'FLSC', 'FIA', 'FDSA'];

  constructor(
    private router: Router,
    private eventService: EventService  
  ) {}

  setMode(mode: string): void {
    this.activeMode = mode;
    this.eventForm.participation_mode = mode;
  }

  toggleUnlimited(): void {
    this.unlimitedAttendees = !this.unlimitedAttendees;
    if (this.unlimitedAttendees) {
      this.eventForm.max_participants = undefined;
    }
  }

  removeFile(index: number): void { this.uploadedFiles.splice(index, 1); }
  removeSponsor(index: number): void { this.sponsors.splice(index, 1); }
  addSponsor(): void { this.sponsors.push({ name: 'Sponsor Nou', website: 'website.com' }); }

  getFileIcon(type: string): string {
    const map: any = { 'pdf': '📄', 'docx': '📝', 'pptx': '📊', 'xlsx': '📈' };
    return map[type] || '📁';
  }

  calculateDuration(): string {
    if (!this.eventForm.start_datetime || !this.eventForm.end_datetime) return '—';
    const start = new Date(this.eventForm.start_datetime);
    const end = new Date(this.eventForm.end_datetime);
    const diff = end.getTime() - start.getTime();
    if (diff <= 0) return '—';
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const parts = [];
    if (days > 0) parts.push(`${days} zi${days > 1 ? 'le' : ''}`);
    if (hours > 0) parts.push(`${hours} ore`);
    return parts.length ? parts.join(', ') : 'Sub 1 oră';
  }

  // Salvează draft — trimite la backend cu status "draft"
  saveDraft(): void {
    if (!this.eventForm.title) {
      this.errorMessage = 'Adaugă cel puțin un titlu!';
      return;
    }

    this.isSaving = true;
    this.errorMessage = '';

    const draftData = { ...this.eventForm, status: 'draft' };

    this.eventService.createEvent(draftData).subscribe({
      next: (response) => {
        this.isSaving = false;
        this.savedMessage = 'Draft salvat!';
        setTimeout(() => this.savedMessage = '', 3000);
      },
      error: (err) => {
        this.isSaving = false;
        this.errorMessage = 'Eroare la salvare!';
      }
    });
  }

  // Publică evenimentul — trimite la backend cu status "active"
  publish(): void {
    if (!this.eventForm.title || !this.eventForm.start_datetime) {
      this.errorMessage = 'Completează cel puțin titlul și data evenimentului!';
      return;
    }

    this.isPublishing = true;
    this.errorMessage = '';

    const publishData = { ...this.eventForm, status: 'active' };

    this.eventService.createEvent(publishData).subscribe({
      next: (response) => {
        this.isPublishing = false;
        this.router.navigate(['/events']);
      },
      error: (err) => {
        this.isPublishing = false;
        this.errorMessage = 'Eroare la publicare!';
      }
    });
  }

  cancel(): void {
    this.router.navigate(['/events']);
  }
  setEntryType(type: string): void {
    this.eventForm.entry_type = type;
  }
}
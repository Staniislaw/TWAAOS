import { Component, Inject, NgZone, OnInit, PLATFORM_ID } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { CommonModule, isPlatformBrowser } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Event, EventFeedback, EventMaterial, EventSponsor } from '../../models/event.model';
import { SidebarComponent } from '../../layout/sidebar-component/sidebar-component';
import { EventService } from '../../services/event-service';
import { Html5Qrcode } from 'html5-qrcode';
import { AuthService } from '../../services/auth';

@Component({
  selector: 'app-event-detail-component',
  standalone: true,
  imports: [CommonModule, FormsModule, SidebarComponent],
  templateUrl: './event-detail-component.html',
  styleUrl: './event-detail-component.css',
})
export class EventDetailComponent implements OnInit {
  event: Event | null = null;
  isRegistered = false;
  materials: EventMaterial[] = [];
  feedbacks: EventFeedback[] = [];
  sponsors: EventSponsor[] = [];
  isLoading = false;
  errorMessage = '';
  newComment = '';
  selectedRating = 0;
  hoverRating = 0;

  //QR CODE
  showQrModal = false;
  qrCodeImage = '';
  qrToken = '';
  isLoadingQr = false;
  manualToken: string = '';
  scanResult: string = '';
  userRole: string | null = null;


  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private eventService: EventService,
    @Inject(PLATFORM_ID) private platformId: Object,
    private authService: AuthService
  ) {}

  ngOnInit(): void {
    this.userRole = this.authService.getUserRole();
    this.route.paramMap.subscribe(params => {
      const id = Number(params.get('id'));
      if (!id || isNaN(id)) return;
      this.loadEvent(id);
      this.loadRegistrationStatus(id);
    });
  }

  loadEvent(id: number): void {
    this.isLoading = true;
    this.errorMessage = '';

    // Incarcam evenimentul din backend
    this.eventService.getEventById(id).subscribe({
      next: (data) => {
        this.event = data;
        this.isLoading = false;
        // Incarcam materialele, feedback-ul si sponsorii
        this.loadMaterials(id);
        this.loadFeedbacks(id);
        this.loadSponsors(id);
      },
      error: (err) => {
        console.error('Eroare la încărcarea evenimentului:', err);
        this.errorMessage = 'Evenimentul nu a putut fi încărcat!';
        this.isLoading = false;
      }
    });
  }
  loadRegistrationStatus(eventId: number): void {
    this.eventService.isRegistered(eventId).subscribe({
      next: (res) => {
        this.isRegistered = res.registered;
      },
      error: () => {
        this.isRegistered = false;
      }
    });
  }
  loadMaterials(id: number): void {
    this.eventService.getEventMaterials(id).subscribe({
      next: (data) => this.materials = data,
      error: () => this.materials = []
    });
  }

  loadFeedbacks(id: number): void {
    this.eventService.getEventFeedback(id).subscribe({
      next: (data) => this.feedbacks = data,
      error: () => this.feedbacks = []
    });
  }

  loadSponsors(id: number): void {
    this.eventService.getEventSponsors(id).subscribe({
      next: (data) => this.sponsors = data,
      error: () => this.sponsors = []
    });
  }
  toggleRegistration(): void {
    if (this.isRegistered) {
      this.unregister();
    } else {
      this.register();
    }
  }
  register(): void {
    if (!this.event) return;
    this.eventService.registerToEvent(this.event.id).subscribe({
      next: () => this.isRegistered = true,
    });
  }
  unregister(): void {
    if (!this.event) return;

    this.eventService.unregisterFromEvent(this.event.id).subscribe({
      next: () => {
        this.isRegistered = false;
      },
      error: () => {
        console.error("Eroare la dezabonare");
      }
    });
  }

  submitFeedback(): void {
    if (this.selectedRating === 0 || !this.newComment.trim() || !this.event) return;

    this.eventService.submitFeedback(
      this.event.id,
      this.selectedRating,
      this.newComment
    ).subscribe({
      next: (newFeedback) => {
        this.feedbacks.unshift(newFeedback);
        this.newComment = '';
        this.selectedRating = 0;
      },
      error: () => {
        // Adaugam local daca backend-ul nu are endpoint inca
        const newFeedback: EventFeedback = {
          id: this.feedbacks.length + 1,
          event_id: this.event!.id,
          user_id: 1,
          rating: this.selectedRating,
          comment: this.newComment,
          created_at: new Date().toISOString()
        };
        this.feedbacks.unshift(newFeedback);
        this.newComment = '';
        this.selectedRating = 0;
      }
    });
  }

  goBack(): void {
    this.router.navigate(['/events']);
  }

  getAverageRating(): number {
    if (!this.feedbacks.length) return 0;
    return Math.round(
      this.feedbacks.reduce((sum, f) => sum + f.rating, 0) / this.feedbacks.length * 10
    ) / 10;
  }

  getFileIcon(type: string): string {
    const map: any = { 'pdf': '📄', 'docx': '📝', 'pptx': '📊', 'xlsx': '📈' };
    return map[type] || '📁';
  }

  getFileSize(kb: number): string {
    return kb >= 1000 ? (kb / 1024).toFixed(1) + ' MB' : kb + ' KB';
  }

  formatDate(dateStr: string): string {
    if (!dateStr) return '—';
    return new Date(dateStr).toLocaleDateString('ro-RO', {
      day: 'numeric', month: 'long', year: 'numeric',
      hour: '2-digit', minute: '2-digit'
    });
  }

  getCoverColor(category: string): string {
    const map: any = {
      'Technology': '#667eea, #764ba2',
      'Science':    '#11998e, #38ef7d',
      'Design':     '#f093fb, #f5576c',
      'Academic':   '#4facfe, #00f2fe',
      'Research':   '#43e97b, #38f9d7',
    };
    return map[category] || '#667eea, #764ba2';
  }

  getCategoryEmoji(category: string): string {
    const map: any = {
      'Technology': '💻', 'Science': '🔬',
      'Design': '🎨', 'Academic': '🎓', 'Research': '📊'
    };
    return map[category] || '📅';
  }

  getStars(rating: number): number[] {
    return Array(5).fill(0).map((_, i) => i + 1);
  }
  getEntryTypeLabel(entryType: string): string {
    const map: any = {
      'free':         '🟢 Intrare liberă',
      'registration': '📝 Necesită înscriere',
      'qr_code':      '🎫 Bilet QR'
    };
    return map[entryType] || '—';
  }
  getEntryTypeClass(entryType: string): object {
    return {
      'tag-free':         entryType === 'free',
      'tag-registration': entryType === 'registration',
      'tag-qr':           entryType === 'qr_code'
    };
  }
  openMyQr(): void {
    this.isLoadingQr = true;
    this.eventService.getMyQr(this.event?.id || 0).subscribe({
      next: (response) => {
        this.qrCodeImage = response.qr_code;
        this.qrToken = response.qr_token;
        this.showQrModal = true;
        this.isLoadingQr = false;
      },
      error: () => {
        this.isLoadingQr = false;
      }
    });
  }

  closeQrModal(): void {
    this.showQrModal = false;
  }
  verifyManual(eventId: number) {
    this.eventService.verifyQr(eventId, this.manualToken).subscribe({
      next: (res) => {
        this.scanResult = "✅" + res.message;
      },
      error: (err) => {
        this.scanResult = "❌" + err.error.detail;
      }
    });
  }
  startScanner(eventId: number) {
    const qr = new Html5Qrcode("qr-reader");

    qr.start(
      { facingMode: "environment" },
      { fps: 10, qrbox: 250 },
      (decodedText) => {
        console.log("Scanat:", decodedText);
        qr.stop(); 
        this.eventService.verifyQr(eventId, decodedText).subscribe({
          next: (res) => {
            this.scanResult = res.message;
          },
          error: (err) => {
            this.scanResult = err.error.detail;
          }
        });
      },
      (err) => {}
    );
  }

  downloadMaterial(material: EventMaterial): void {
    const fileUrl = `http://localhost:8000/${material.file_path}`;
    const link = document.createElement('a');
    link.href = fileUrl;
    link.download = material.file_name;
    link.target = '_blank';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }
  // Google Calendar
  addToGoogleCalendar(): void {
    if (!this.event) return;

    const start = new Date(this.event.start_datetime)
      .toISOString().replace(/-|:|\.\d{3}/g, '');
    const end = this.event.end_datetime
      ? new Date(this.event.end_datetime).toISOString().replace(/-|:|\.\d{3}/g, '')
      : start;

    const params = new URLSearchParams({
      action: 'TEMPLATE',
      text: this.event.title,
      dates: `${start}/${end}`,
      details: this.event.description || '',
      location: this.event.location || '',
    });

    const url = `https://calendar.google.com/calendar/render?${params.toString()}`;
    window.open(url, '_blank');
  }

  // Export .ics
  exportIcs(): void {
    if (!this.event) return;

    const start = new Date(this.event.start_datetime)
      .toISOString().replace(/-|:|\.\d{3}/g, '');
    const end = this.event.end_datetime
      ? new Date(this.event.end_datetime).toISOString().replace(/-|:|\.\d{3}/g, '')
      : start;

    const ics = [
      'BEGIN:VCALENDAR',
      'VERSION:2.0',
      'PRODID:-//USV Events//RO',
      'BEGIN:VEVENT',
      `UID:event-${this.event.id}@usv.ro`,
      `DTSTAMP:${new Date().toISOString().replace(/-|:|\.\d{3}/g, '')}`,
      `DTSTART:${start}`,
      `DTEND:${end}`,
      `SUMMARY:${this.event.title}`,
      `DESCRIPTION:${(this.event.description || '').replace(/\n/g, '\\n')}`,
      `LOCATION:${this.event.location || ''}`,
      'END:VEVENT',
      'END:VCALENDAR'
    ].join('\r\n');

    const blob = new Blob([ics], { type: 'text/calendar;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${this.event.title.replace(/\s+/g, '_')}.ics`;
    link.click();
    URL.revokeObjectURL(url);
  }
}
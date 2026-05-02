import { Component } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Event, EventMaterial } from '../../models/event.model';
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

  categories = ['academic','sport', 'cariera', 'voluntariat'];
  faculties = ['FIESC', 'FSE', 'FSEAP', 'FLSC', 'FIA', 'FDSA'];
  uploadedFiles: { file: File, name: string, size: string, type: string }[] = [];
  sponsors: { id?: number, name: string, logo_url: string, website_url: string }[] = [];
  showSponsorDialog = false;
  sponsorForm = { name: '', logo_url: '', website_url: '' };
  sponsorPreviewError = false;
  createdEventId: number | null = null;

  isEditMode = false;
  editEventId: number | null = null;
  existingMaterials: EventMaterial[] = [];
  materialsToDelete: number[] = [];

  sponsorsToDelete: number[] = [];
  newSponsors: { name: string, logo_url: string, website_url: string }[] = [];



  constructor(
    private router: Router,
    private route: ActivatedRoute,
    private eventService: EventService  
  ) {}
  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      this.isEditMode = true;
      this.editEventId = +id;
      this.eventService.getEventById(+id).subscribe({
        next: (event) => {
          this.eventForm = {
            ...event,
            start_datetime: this.toDatetimeLocal(event.start_datetime),
            end_datetime: event.end_datetime ? this.toDatetimeLocal(event.end_datetime) : '',
            registration_deadline: event.registration_deadline
              ? event.registration_deadline.split('T')[0].split(' ')[0] : '',
          };
          this.activeMode = event.participation_mode || 'In-Person';
          this.sponsors = (event.sponsors || []).map((s: any) => ({
            id: s.id,       
            name: s.name,
            logo_url: s.logo_path,
            website_url: s.website_url
          }));
          this.existingMaterials = event.materials || [];
        }
      });
    }
  }
  toDatetimeLocal(dateStr: string): string {
    if (!dateStr) return '';
    return dateStr.replace(' ', 'T').substring(0, 16);
  }

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

  getFileIcon(type: string): string {
    const map: any = { 'pdf': '📄', 'docx': '📝', 'pptx': '📊', 'xlsx': '📈' };
    return map[type] || '📁';
  }
  getFileSize(kb: number | undefined): string {
   if (!kb) return '—';
     return kb >= 1000 ? (kb / 1024).toFixed(1) + ' MB' : kb + ' KB';
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

    const call = this.isEditMode && this.editEventId
      ? this.eventService.updateEvent(this.editEventId, { ...this.eventForm, status: 'draft' })
      : this.eventService.createEvent({ ...this.eventForm, status: 'draft' });

    call.subscribe({
      next: (response) => {
        const id = this.isEditMode ? this.editEventId! : response.id;
        this.uploadExtras(id, () => {
          this.isSaving = false;
          this.savedMessage = 'Draft salvat!';
          setTimeout(() => this.savedMessage = '', 3000);
        });
      },
      error: () => {
        this.isSaving = false;
        this.errorMessage = 'Eroare la salvare!';
      }
    });
  }


  // Publică evenimentul — trimite la backend cu status "active"
  publish(): void {
    if (!this.eventForm.title || !this.eventForm.start_datetime) {
      this.errorMessage = 'Completează titlul și data!';
      return;
    }
    this.isPublishing = true;

    if (this.isEditMode && this.editEventId) {
      // UPDATE
      this.eventService.updateEvent(this.editEventId, this.eventForm).subscribe({
        next: async (response) => {
          // Ștergi materialele marcate
          for (const materialId of this.materialsToDelete) {
            await this.eventService.deleteMaterial(this.editEventId!, materialId).toPromise();
          }
          for (const sponsorId of this.sponsorsToDelete) {
            await this.eventService.deleteSponsor(this.editEventId!, sponsorId).toPromise();
          }
          const newSponsors = this.sponsors.filter(s => !s.id);
          for (const sponsor of newSponsors) {
            await this.eventService.addSponsor(this.editEventId!, sponsor).toPromise();
          }

          // Uploadezi materialele noi
          if (this.uploadedFiles.length > 0) {
            const files = this.uploadedFiles.map(f => f.file);
            await this.eventService.uploadMaterials(this.editEventId!, files).toPromise();
          }
          this.isPublishing = false;
          this.router.navigate(['/events']);
        },
        error: () => {
          this.isPublishing = false;
          this.errorMessage = 'Eroare la salvare!';
        }
      });
    } else {
      this.eventService.createEvent({ ...this.eventForm, status: 'active' }).subscribe({
        next: (response) => {
          this.uploadExtras(response.id, () => {
            this.isPublishing = false;
            this.savedMessage = 'Eveniment trimis! Așteaptă aprobarea adminului.';
            setTimeout(() => this.router.navigate(['/events']), 2000);
          });
        },
        error: () => {
          this.isPublishing = false;
          this.errorMessage = 'Eroare la publicare!';
        }
      });
    }
  }

  uploadExtras(eventId: number, onDone: () => void): void {
    const sponsorsToAdd = this.isEditMode
      ? this.sponsors.filter(s => !s.id)
      : this.sponsors;

    const sponsorCalls = sponsorsToAdd.map(s =>
      this.eventService.addSponsor(eventId, s).toPromise()
    );

    Promise.all(sponsorCalls).then(() => {
      if (this.uploadedFiles.length > 0) {
        const files = this.uploadedFiles.map(f => f.file);
        this.eventService.uploadMaterials(eventId, files).subscribe({
          next: () => onDone(),
          error: () => onDone()
        });
      } else {
        onDone();
      }
    });
  }


  cancel(): void {
    this.router.navigate(['/events']);
  }
  setEntryType(type: string): void {
    this.eventForm.entry_type = type;
  }
  onFileDragOver(event: DragEvent): void {
    event.preventDefault();
  }

  onFileDrop(event: DragEvent): void {
    event.preventDefault();
    const files = event.dataTransfer?.files;
    if (files) this.addFiles(Array.from(files));
  }

  onFileSelect(event: any): void {
    this.addFiles(Array.from(event.target.files));
  }

  addFiles(files: File[]): void {
    const allowed = ['pdf', 'pptx', 'docx', 'zip'];
    for (const file of files) {
      const ext = file.name.split('.').pop()?.toLowerCase() || '';
      if (!allowed.includes(ext)) continue;
      if (file.size > 50 * 1024 * 1024) continue;
      this.uploadedFiles.push({
        file,
        name: file.name,
        size: this.formatSize(file.size),
        type: ext
      });
    }
  }

  formatSize(bytes: number): string {
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  }

  removeFile(index: number): void {
    this.uploadedFiles.splice(index, 1);
  }
  openSponsorDialog(): void {
    this.sponsorForm = { name: '', logo_url: '', website_url: '' };
    this.showSponsorDialog = true;
  }

  addSponsor(): void {
    this.sponsorForm = { name: '', logo_url: '', website_url: '' };
    this.sponsorPreviewError = false;
    this.showSponsorDialog = true;
  }

  confirmSponsor(): void {
    if (!this.sponsorForm.name) return;
    this.sponsors.push({ ...this.sponsorForm });
    this.showSponsorDialog = false;
  }


  cancelSponsor(): void {
    this.showSponsorDialog = false;
  }

  removeSponsor(index: number): void {
    const sponsor = this.sponsors[index];
    if (sponsor.id) {
      this.sponsorsToDelete.push(sponsor.id);
    }
    this.sponsors.splice(index, 1);
  }
  onLogoError(): void {
    this.sponsorPreviewError = true;
  }
  removeExistingMaterial(index: number): void {
    const material = this.existingMaterials[index];
    this.materialsToDelete.push(material.id);   
    this.existingMaterials.splice(index, 1);      
  }
}
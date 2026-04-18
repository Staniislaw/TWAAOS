import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Event } from '../../models/event.model';
import { SidebarComponent } from '../../layout/sidebar-component/sidebar-component';
import { EventService } from '../../services/event-service';

@Component({
  selector: 'app-events-component',
  standalone: true,
  imports: [CommonModule, FormsModule, SidebarComponent],
  templateUrl: './events-component.html',
  styleUrl: './events-component.css',
})
export class EventsComponent implements OnInit {
  events: Event[] = [];
  //evenimente la care sunt deja inregistrat
  registeredEventIds = new Set<number>();

  filteredEvents: Event[] = [];
  isLoading = true;
  errorMessage = '';

  categories = ['Technology', 'Science', 'Design', 'Academic', 'Research', 'Arts'];
  faculties = ['FIESC', 'FSE', 'FSEAP', 'FLSC', 'FIA', 'FDSA'];
  modes = ['In-Person', 'Online', 'Hybrid'];
  statuses = ['active', 'closing_soon', 'closed'];

  //QR
  showQrModal = false;
  qrCodeImage = '';
  qrToken = '';

  //FILTERS
  selectedCategory = '';
  selectedFaculty = '';
  selectedMode = '';  
  selectedStatus = '';
  selectedOrganizer = '';
  selectedLocation = '';
  selectedEntryType = '';
  searchDateFrom = '';
  searchDateTo = '';

  sortOrder: 'newest' | 'oldest' = 'newest'; 

  constructor(
    private router: Router,
    private eventService: EventService
  ) {}

  ngOnInit(): void {
    this.loadEvents();
  }

  loadEvents(): void {
    this.isLoading = true;
    this.errorMessage = '';

    this.eventService.getEvents().subscribe({
      next: (data) => {
        this.events = data;
        this.filteredEvents = data;
        this.eventService.getMyRegisteredEventIds().subscribe({
          next: (ids) => {
            this.registeredEventIds = new Set(ids);
            this.isLoading = false;
          }
        });
        this.filteredEvents = data;
        this.isLoading = false;
      },
      error: (err) => {
        this.errorMessage = 'Nu s-au putut încărca evenimentele!';
        this.isLoading = false;
      }
    });
  }
  isRegistered(eventId: number): boolean {
    return this.registeredEventIds.has(eventId);
  }
  register(eventId: number): void {
    if (!eventId) return;
    this.eventService.registerToEvent(eventId).subscribe({
      next: (response) => {
        this.registeredEventIds.add(eventId);
        
        // dacă backend-ul a returnat QR, deschide modalul
        if (response.qr_code) {
          this.qrCodeImage = response.qr_code;
          this.qrToken = response.qr_token;
          this.showQrModal = true;
        }
      },
      error: () => {}
    });
  }

  closeQrModal(): void {
    this.showQrModal = false;
    this.qrCodeImage = '';
    this.qrToken = '';
  }


  goToEvent(id: number): void {
    this.router.navigate(['/events', id]);
  }

  getCategoryEmoji(category: string): string {
    const map: any = {
      'Technology': '💻', 'Science': '🔬',
      'Design': '🎨', 'Academic': '🎓',
      'Research': '📊', 'Arts': '🎭'
    };
    return map[category] || '📅';
  }

  getStatusLabel(status: string): string {
    const map: any = {
      'active': 'Deschis',
      'closing_soon': 'Se închide curând',
      'closed': 'Închis',
      'cancelled': 'Anulat',
      'draft': 'Draft'
    };
    return map[status] || status;
  }

  getModeIcon(mode: string): string {
    const map: any = {
      'In-Person': '📍', 'Online': '💻', 'Hybrid': '🔄'
    };
    return map[mode] || '📅';
  }

  formatDate(dateStr: string): string {
    if (!dateStr) return '—';
    const date = new Date(dateStr);
    return date.toLocaleDateString('ro-RO', {
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
      'Arts':       '#fa709a, #fee140'
    };
    return map[category] || '#667eea, #764ba2';
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

  // Liste dinamice din date reale
  get availableCategories(): string[] {
    return [...new Set(this.events.map(e => e.category).filter(Boolean))] as string[];
  }
  get availableFaculties(): string[] {
    return [...new Set(this.events.map(e => e.faculty).filter(Boolean))] as string[];
  }
  get availableLocations(): string[] {
    return [...new Set(this.events.map(e => e.location).filter(Boolean))] as string[];
  }
  get availableOrganizers(): string[] {
    return [...new Set(this.events.map(e => e.organizer_name).filter(Boolean))] as string[];
  }
  toggleSort(): void {
    this.sortOrder = this.sortOrder === 'newest' ? 'oldest' : 'newest';
    this.applyFilters();
  }

  // Filtrare evenimente
  applyFilters(): void {
    this.currentPage = 1; 
    let filtered = this.events.filter(event => {
      // Categorie
      const matchCategory = !this.selectedCategory || event.category === this.selectedCategory;
      // Facultate
      const matchFaculty = !this.selectedFaculty || event.faculty === this.selectedFaculty;
      // Mod participare
      const matchMode = !this.selectedMode || event.participation_mode === this.selectedMode;
      // Status
      const matchStatus = !this.selectedStatus || event.status === this.selectedStatus;
      // Organizator
      const matchOrganizer = !this.selectedOrganizer || event.organizer_name === this.selectedOrganizer;
      // Locatie
      const matchLocation = !this.selectedLocation || event.location === this.selectedLocation;
      // Entry type (intrare liberă / înscriere / QR)
      const matchEntryType = !this.selectedEntryType || event.entry_type === this.selectedEntryType;
      // Data — de la
      const matchDateFrom = !this.searchDateFrom ||
        new Date(event.start_datetime) >= new Date(this.searchDateFrom);
      // Data — până la
      const matchDateTo = !this.searchDateTo ||
        new Date(event.start_datetime) <= new Date(this.searchDateTo);

      return matchCategory && matchFaculty && matchMode && matchStatus
          && matchOrganizer && matchLocation && matchEntryType
          && matchDateFrom && matchDateTo;
    });
    filtered.sort((a, b) => {
        const dateA = new Date(a.created_at).getTime();
        const dateB = new Date(b.created_at).getTime();
        return this.sortOrder === 'newest' ? dateB - dateA : dateA - dateB;
      });
    this.filteredEvents = filtered;
  }

  resetFilters(): void {
    this.currentPage = 1;
    this.selectedCategory = '';
    this.selectedFaculty = '';
    this.selectedMode = '';
    this.selectedStatus = '';
    this.selectedOrganizer = '';
    this.selectedLocation = '';
    this.selectedEntryType = '';
    this.searchDateFrom = '';
    this.searchDateTo = '';
    this.filteredEvents = this.events;
  }

  //PAGINARE
  currentPage = 1;
  pageSize = 5; // cate carduri pe pagina

  get totalPages(): number {
    return Math.ceil(this.filteredEvents.length / this.pageSize);
  }

  get paginatedEvents(): Event[] {
    const start = (this.currentPage - 1) * this.pageSize;
    return this.filteredEvents.slice(start, start + this.pageSize);
  }

  get pageNumbers(): number[] {
    return Array.from({ length: this.totalPages }, (_, i) => i + 1);
  }

  goToPage(page: number): void {
    if (page < 1 || page > this.totalPages) return;
    this.currentPage = page;
  }
}
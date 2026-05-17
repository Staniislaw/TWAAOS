// admin-component.ts
import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { SidebarComponent } from '../../layout/sidebar-component/sidebar-component';
import { AdminService } from '../../services/admin.service';
import jsPDF from 'jspdf';

@Component({
  selector: 'app-admin',
  standalone: true,
  imports: [CommonModule, FormsModule, SidebarComponent],
  templateUrl: './admin-component.html',
  styleUrl: './admin-component.css'
})
export class AdminComponent implements OnInit {
  reports: any = null;
  isLoadingReports = false;
  rejectedEvents: any[] = [];
  isLoadingRejected = false;
  activeTab: 'users' | 'events' | 'rejected'|'reports'| 'scraper' = 'users';
  // Users
  users: any[] = [];
  filteredUsers: any[] = [];
  searchUser = '';
  isLoadingUsers = true;

  // Events
  pendingEvents: any[] = [];
  isLoadingEvents = true;

  // Dialog reject
  showRejectDialog = false;
  rejectEventId: number | null = null;
  rejectReason = '';

  // Dialog event preview
  showEventPreview = false;
  previewEvent: any = null;

  scrapedEvents: any[] = [];
  isLoadingScrape = false;
  scrapeUrl = 'https://www.orasulsuceava.ro/evenimente/';
  scrapeError = '';
  showScrapeResult = false;

  importedEventIds: Set<number> = new Set();
  isImporting: Set<number> = new Set();


  constructor(
    private adminService: AdminService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.loadUsers();
    this.loadPendingEvents();
    this.loadRejectedEvents();
    this.loadReports();
  }

  // ── USERS ──
  loadUsers(): void {
    this.adminService.getUsers().subscribe({
      next: (data) => {
        this.users = data;
        this.filteredUsers = data;
        this.isLoadingUsers = false;
      },
      error: () => this.isLoadingUsers = false
    });
  }

  searchUsers(): void {
    const q = this.searchUser.toLowerCase();
    this.filteredUsers = this.users.filter(u =>
      u.full_name?.toLowerCase().includes(q) ||
      u.email?.toLowerCase().includes(q)
    );
  }

  updateRole(userId: number, role: string): void {
    this.adminService.updateUserRole(userId, role).subscribe({
      next: () => {
        const user = this.users.find(u => u.id === userId);
        if (user) user.role = role;
      }
    });
  }

  toggleActive(userId: number): void {
    this.adminService.toggleUserActive(userId).subscribe({
      next: (res) => {
        const user = this.users.find(u => u.id === userId);
        if (user) user.is_active = res.is_active;
      }
    });
  }

  getRoleClass(role: string): string {
    const map: any = {
      'admin':     'role-admin',
      'organizer': 'role-organizer',
      'student':   'role-student'
    };
    return map[role] || '';
  }

  // ── EVENTS ──
  loadPendingEvents(): void {
    this.adminService.getPendingEvents().subscribe({
      next: (data) => {
        this.pendingEvents = data;
        this.isLoadingEvents = false;
      },
      error: () => this.isLoadingEvents = false
    });
  }

  openPreview(event: any): void {
    this.previewEvent = event;
    this.showEventPreview = true;
  }

  closePreview(): void {
    this.showEventPreview = false;
    this.previewEvent = null;
  }

  approveEvent(eventId: number): void {
    this.adminService.decideEvent(eventId, 'approve').subscribe({
      next: () => {
        this.pendingEvents = this.pendingEvents.filter(e => e.id !== eventId);
        this.closePreview();
      }
    });
  }

  openRejectDialog(eventId: number): void {
    this.rejectEventId = eventId;
    this.rejectReason = '';
    this.showRejectDialog = true;
  }

  confirmReject(): void {
    if (!this.rejectReason.trim() || !this.rejectEventId) return;
    this.adminService.decideEvent(this.rejectEventId, 'reject', this.rejectReason).subscribe({
      next: () => {
        this.pendingEvents = this.pendingEvents.filter(e => e.id !== this.rejectEventId);
        this.showRejectDialog = false;
        this.rejectEventId = null;
        this.closePreview();
      }
    });
  }

  formatDate(dateStr: string): string {
    if (!dateStr) return '—';
    return new Date(dateStr).toLocaleDateString('ro-RO', {
      day: 'numeric', month: 'long', year: 'numeric'
    });
  }

  getEntryTypeLabel(type: string): string {
    const map: any = {
      'free': '🟢 Intrare liberă',
      'registration': '📝 Înscriere',
      'qr_code': '🎫 QR Code'
    };
    return map[type] || type;
  }
  loadRejectedEvents(): void {
    this.isLoadingRejected = true;
    this.adminService.getRejectedEvents().subscribe({
      next: (data) => {
        this.rejectedEvents = data;
        this.isLoadingRejected = false;
      },
      error: () => this.isLoadingRejected = false
    });
  }
  approveFromRejected(eventId: number): void {
    this.adminService.decideEvent(eventId, 'approve').subscribe({
      next: () => {
        this.rejectedEvents = this.rejectedEvents.filter(e => e.id !== eventId);
        this.closePreview();
      }
    });
  }
  loadReports(): void {
    this.isLoadingReports = true;
    this.adminService.getReports().subscribe({
      next: (data) => {
        this.reports = data;
        this.isLoadingReports = false;
      },
      error: () => this.isLoadingReports = false
    });
  }
  getMonthName(month: number): string {
    const months = ['Ian', 'Feb', 'Mar', 'Apr', 'Mai', 'Iun',
                    'Iul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    return months[month - 1];
  }

  getStatusLabel(status: string): string {
    const map: any = {
      'active':   '✅ Active',
      'pending':  '⏳ În așteptare',
      'rejected': '❌ Respinse',
      'draft':    '📝 Draft',
      'closed':   '🔒 Închise'
    };
    return map[status] || status;
  }

  getMaxCount(arr: any[]): number {
    return Math.max(...arr.map(i => i.count), 1);
  }
  exportPdf(): void {
    if (!this.reports) return;

    const doc = new jsPDF();
    const pageWidth = doc.internal.pageSize.getWidth();
    let y = 20;

    // ── Header ──
    doc.setFillColor(0, 61, 155);
    doc.rect(0, 0, pageWidth, 40, 'F');
    doc.setTextColor(255, 255, 255);
    doc.setFontSize(20);
    doc.setFont('helvetica', 'bold');
    doc.text('Raport Evenimente USV', pageWidth / 2, 18, { align: 'center' });
    doc.setFontSize(10);
    doc.setFont('helvetica', 'normal');
    doc.text(`Generat: ${new Date().toLocaleDateString('ro-RO')}`, pageWidth / 2, 30, { align: 'center' });

    y = 55;
    doc.setTextColor(0, 0, 0);

    // ── Statistici generale ──
    doc.setFontSize(13);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(0, 61, 155);
    doc.text('Statistici Generale', 14, y);
    y += 8;

    const stats = [
      ['Total evenimente', this.reports.general.total_events],
      ['Total utilizatori', this.reports.general.total_users],
      ['Total înregistrări', this.reports.general.total_registrations],
      ['Total feedback-uri', this.reports.general.total_feedback],
      ['Rating mediu', `${this.reports.general.avg_rating}/5`],
      ['Participare medie / eveniment', this.reports.general.avg_participation],
    ];

    doc.setFontSize(10);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(0, 0, 0);

    stats.forEach(([label, value], i) => {
      const isEven = i % 2 === 0;
      if (isEven) doc.setFillColor(247, 249, 251);
      else doc.setFillColor(255, 255, 255);
      doc.rect(14, y - 4, pageWidth - 28, 8, 'F');
      doc.text(String(label), 16, y);
      doc.setFont('helvetica', 'bold');
      doc.text(String(value), pageWidth - 16, y, { align: 'right' });
      doc.setFont('helvetica', 'normal');
      y += 9;
    });

    y += 8;

    // ── Evenimente pe lună ──
    doc.setFontSize(13);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(0, 61, 155);
    doc.text('Evenimente pe Luna', 14, y);
    y += 8;

    doc.setFontSize(10);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(0, 0, 0);

    this.reports.events_per_month.forEach((item: any, i: number) => {
      if (this.isEven(i)) doc.setFillColor(247, 249, 251);
      else doc.setFillColor(255, 255, 255);
      doc.rect(14, y - 4, pageWidth - 28, 8, 'F');
      doc.text(`${this.getMonthName(item.month)} ${item.year}`, 16, y);
      doc.setFont('helvetica', 'bold');
      doc.text(String(item.count), pageWidth - 16, y, { align: 'right' });
      doc.setFont('helvetica', 'normal');
      y += 9;
      if (y > 260) { doc.addPage(); y = 20; }
    });

    y += 8;

    // ── Top organizatori ──
    if (y > 220) { doc.addPage(); y = 20; }

    doc.setFontSize(13);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(0, 61, 155);
    doc.text('Top Organizatori', 14, y);
    y += 8;

    doc.setFontSize(10);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(0, 0, 0);

    this.reports.events_per_organizer.forEach((item: any, i: number) => {
      if (this.isEven(i)) doc.setFillColor(247, 249, 251);
      else doc.setFillColor(255, 255, 255);
      doc.rect(14, y - 4, pageWidth - 28, 8, 'F');
      doc.text(`${i + 1}. ${item.name}`, 16, y);
      doc.text(item.email, pageWidth / 2, y, { align: 'center' });
      doc.setFont('helvetica', 'bold');
      doc.text(`${item.count} ev.`, pageWidth - 16, y, { align: 'right' });
      doc.setFont('helvetica', 'normal');
      y += 9;
      if (y > 260) { doc.addPage(); y = 20; }
    });

    y += 8;

    // ── Evenimente pe categorie ──
    if (y > 220) { doc.addPage(); y = 20; }

    doc.setFontSize(13);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(0, 61, 155);
    doc.text('Evenimente pe Categorie', 14, y);
    y += 8;

    doc.setFontSize(10);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(0, 0, 0);

    this.reports.events_per_category.forEach((item: any, i: number) => {
      if (this.isEven(i)) doc.setFillColor(247, 249, 251);
      else doc.setFillColor(255, 255, 255);
      doc.rect(14, y - 4, pageWidth - 28, 8, 'F');
      doc.text(item.category, 16, y);
      doc.setFont('helvetica', 'bold');
      doc.text(String(item.count), pageWidth - 16, y, { align: 'right' });
      doc.setFont('helvetica', 'normal');
      y += 9;
    });

    y += 8;

    // ── Evenimente pe status ──
    if (y > 220) { doc.addPage(); y = 20; }

    doc.setFontSize(13);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(0, 61, 155);
    doc.text('Evenimente pe Status', 14, y);
    y += 8;

    doc.setFontSize(10);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(0, 0, 0);

    this.reports.events_per_status.forEach((item: any, i: number) => {
      if (this.isEven(i)) doc.setFillColor(247, 249, 251);
      else doc.setFillColor(255, 255, 255);
      doc.rect(14, y - 4, pageWidth - 28, 8, 'F');
      doc.text(this.getStatusLabel(item.status), 16, y);
      doc.setFont('helvetica', 'bold');
      doc.text(String(item.count), pageWidth - 16, y, { align: 'right' });
      doc.setFont('helvetica', 'normal');
      y += 9;
    });

    // ── Footer ──
    const totalPages = doc.getNumberOfPages();
    for (let i = 1; i <= totalPages; i++) {
      doc.setPage(i);
      doc.setFontSize(8);
      doc.setTextColor(150, 150, 150);
      doc.text(
        `USV Academic Events Platform — Pagina ${i} din ${totalPages}`,
        pageWidth / 2,
        doc.internal.pageSize.getHeight() - 8,
        { align: 'center' }
      );
    }

    doc.save(`raport_evenimente_${new Date().toISOString().split('T')[0]}.pdf`);
  }

  // helper
  private isEven(n: number): boolean {
    return n % 2 === 0;
  }
  scrapeEvents(): void {
    this.isLoadingScrape = true;
    this.scrapeError = '';
    this.scrapedEvents = [];
    
    this.adminService.scrapeEvents(this.scrapeUrl).subscribe({
      next: (res) => {
        this.scrapedEvents = res.events;
        this.showScrapeResult = true;
        this.isLoadingScrape = false;
      },
      error: (err) => {
        this.scrapeError = err.error?.detail || 'Eroare la scraping.';
        this.isLoadingScrape = false;
      }
    });
  }
  importEvent(event: any, index: number): void {
    this.isImporting.add(index);
    this.adminService.importScrapedEvent(event).subscribe({
      next: () => {
        this.importedEventIds.add(index);
        this.isImporting.delete(index);
      },
      error: (err) => {
        console.error('Eroare import:', err);
        this.isImporting.delete(index);
      }
    });
  }
  editScrapedEvent(ev: any): void {
    const description = ev.price 
      ? `${ev.description || ''}\n💰 Preț: ${ev.price}`.trim()
      : ev.description;

    sessionStorage.setItem('scraped_event', JSON.stringify({
      title: ev.title,
      description: description,
      start_datetime: ev.start_datetime,
      location: ev.location,
      entry_type: ev.entry_type === 'free' ? 'free' : 'registration',
    }));
    this.router.navigate(['/events/create']);
  }
}
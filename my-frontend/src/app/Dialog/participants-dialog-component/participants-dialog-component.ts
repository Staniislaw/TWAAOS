import { Component, Inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MAT_DIALOG_DATA, MatDialogRef, MatDialogModule } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { EventService } from '../../services/event-service';

@Component({
  selector: 'app-participants-dialog',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './participants-dialog-component.html',
  styleUrl: './participants-dialog-component.css'
})
export class ParticipantsDialogComponent implements OnInit {
  participants: any[] = [];
  isLoading = true;

  constructor(
    @Inject(MAT_DIALOG_DATA) public data: { eventId: number, eventTitle: string },
    @Inject(MatDialogRef) private dialogRef: MatDialogRef<ParticipantsDialogComponent>,
    private eventService: EventService
  ) {}


  ngOnInit(): void {
    this.eventService.getParticipants(this.data.eventId).subscribe({
      next: (data) => {
        this.participants = data;
        this.isLoading = false;
      },
      error: () => this.isLoading = false
    });
  }

  close(): void {
    this.dialogRef.close();
  }

  countByStatus(status: string): number {
    return this.participants.filter(p => p.status === status).length;
  }

  getStatusLabel(status: string, position: number | null): string {
    if (status === 'registered') return '✅ Înregistrat';
    if (status === 'waitlist')   return `⏳ Waitlist #${position}`;
    if (status === 'attended')   return '🎫 Prezent';
    if (status === 'cancelled')  return '❌ Anulat';
    return status;
  }

  getStatusClass(status: string): string {
    const map: any = {
      'registered': 'status-registered',
      'waitlist':   'status-waitlist',
      'attended':   'status-attended',
      'cancelled':  'status-cancelled'
    };
    return map[status] || '';
  }

  formatDate(dateStr: string): string {
    if (!dateStr) return '—';
    return new Date(dateStr).toLocaleDateString('ro-RO', {
      day: 'numeric', month: 'short', year: 'numeric',
      hour: '2-digit', minute: '2-digit'
    });
  }

  exportCsv(): void {
    if (!this.participants.length) return;

    const headers = ['Nume', 'Email', 'Status', 'Înregistrat la', 'Check-in'];
    const rows = this.participants.map(p => [
      p.full_name,
      p.email,
      p.status === 'registered' ? 'Înregistrat' :
      p.status === 'waitlist'   ? `Waitlist #${p.waitlist_position}` :
      p.status === 'attended'   ? 'Prezent' : p.status,
      p.registered_at,
      p.checked_in ? 'Da' : 'Nu'
    ]);

    const csv = [headers, ...rows]
      .map(row => row.map((cell: any) => `"${cell}"`).join(','))
      .join('\n');

    const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `participanti_${this.data.eventTitle.replace(/\s+/g, '_')}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  }
}
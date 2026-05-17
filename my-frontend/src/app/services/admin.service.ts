// services/admin.service.ts
import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class AdminService {
  private apiUrl = 'http://localhost:8000/admin';
private baseUrl = 'http://localhost:8000';
  constructor(private http: HttpClient) {}

  private getHeaders(): HttpHeaders {
    const token = localStorage.getItem('access_token') || '';
    return new HttpHeaders({ Authorization: `Bearer ${token}` });
  }

  getUsers(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/users`, { headers: this.getHeaders() });
  }

  updateUserRole(userId: number, role: string): Observable<any> {
    return this.http.put(`${this.apiUrl}/users/${userId}/role`, { role }, { headers: this.getHeaders() });
  }

  toggleUserActive(userId: number): Observable<any> {
    return this.http.put(`${this.apiUrl}/users/${userId}/toggle-active`, {}, { headers: this.getHeaders() });
  }

  getPendingEvents(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/events/pending`, { headers: this.getHeaders() });
  }

  decideEvent(eventId: number, action: string, rejectionReason?: string): Observable<any> {
    return this.http.put(`${this.apiUrl}/events/${eventId}/decision`, {
      action,
      rejection_reason: rejectionReason || null
    }, { headers: this.getHeaders() });
  }
  getRejectedEvents(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/events/rejected`, { headers: this.getHeaders() });
  }
  getReports(): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/reports`, { headers: this.getHeaders() });
  }
  scrapeEvents(url?: string): Observable<any> {
    const params = url ? `?url=${encodeURIComponent(url)}` : '';
    return this.http.get<any>(`http://localhost:8000/ai-scraper/scrape${params}`, { 
      headers: this.getHeaders() 
    });
  }
  importScrapedEvent(event: any): Observable<any> {
    return this.http.post(`${this.baseUrl}/ai-scraper/import`, event, {
      headers: this.getHeaders()
    });
  }
}
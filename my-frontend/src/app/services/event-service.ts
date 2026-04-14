import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { AuthService } from './auth';
import { EventFeedback, EventMaterial, EventSponsor } from '../models/event.model';

@Injectable({
  providedIn: 'root'
})
export class EventService {
  private apiUrl = 'http://localhost:8000/events';

  constructor(
    private http: HttpClient,
    private authService: AuthService
  ) {}

  private getHeaders(): HttpHeaders {
    const token = this.authService.getToken();
    return new HttpHeaders({
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    });
  }

  // GET toate evenimentele
  getEvents(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/`, {
      headers: this.getHeaders()
    });
  }

  // GET eveniment dupa ID
  getEventById(id: number): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/${id}`, {
      headers: this.getHeaders()
    });
  }

  // POST creaza eveniment
  createEvent(eventData: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/`, eventData, {
      headers: this.getHeaders()
    });
  }

  // PUT updateaza eveniment
  updateEvent(id: number, eventData: any): Observable<any> {
    return this.http.put(`${this.apiUrl}/${id}`, eventData, {
      headers: this.getHeaders()
    });
  }

  // DELETE eveniment
  deleteEvent(id: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/${id}`, {
      headers: this.getHeaders()
    });
  }

    // Materiale eveniment
  getEventMaterials(eventId: number): Observable<EventMaterial[]> {
    return this.http.get<EventMaterial[]>(
      `${this.apiUrl}/${eventId}/materials`,
      { headers: this.getHeaders() }
    );
  }

  // Feedback eveniment
  getEventFeedback(eventId: number): Observable<EventFeedback[]> {
    return this.http.get<EventFeedback[]>(
      `${this.apiUrl}/${eventId}/feedback`,
      { headers: this.getHeaders() }
    );
  }

  // Sponsori eveniment
  getEventSponsors(eventId: number): Observable<EventSponsor[]> {
    return this.http.get<EventSponsor[]>(
      `${this.apiUrl}/${eventId}/sponsors`,
      { headers: this.getHeaders() }
    );
  }

  // Inregistrare la eveniment
  registerToEvent(eventId: number): Observable<any> {
    return this.http.post(
      `${this.apiUrl}/${eventId}/register`, {},
      { headers: this.getHeaders() }
    );
  }

  // Trimite feedqback
  submitFeedback(eventId: number, rating: number, comment: string): Observable<any> {
    return this.http.post(
      `${this.apiUrl}/${eventId}/feedback`,
      { rating, comment },
      { headers: this.getHeaders() }
    );
  }

  getMyRegisteredEventIds(): Observable<number[]> {
    return this.http.get<number[]>(`${this.apiUrl}/my/ids`, {
      headers: this.getHeaders()
    });
  }
  isRegistered(eventId: number): Observable<{ registered: boolean }> {
    return this.http.get<{ registered: boolean }>(
      `${this.apiUrl}/${eventId}/is-registered`,
      { headers: this.getHeaders() }
    );
  }

  getMyQr(eventId: number): Observable<any> {
    return this.http.get(
      `${this.apiUrl}/${eventId}/my-qr`,
      { headers: this.getHeaders() }
    );
  }

  verifyQr(eventId: number, token: string): Observable<any> {
    return this.http.post(
      `${this.apiUrl}/${eventId}/verify-qr`,
      { token },
      { headers: this.getHeaders() }
    );
  }
}
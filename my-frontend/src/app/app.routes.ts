import { Routes } from '@angular/router';
import { LoginComponent } from './pages/login/login-component';
import { HomeComponent } from './pages/home-component/home-component';
import { EventsComponent } from './pages/events-component/events-component';
import { EventDetailComponent } from './pages/event-detail-component/event-detail-component';
import { CreateEventComponent } from './pages/create-event-component/create-event-component';
import { AuthCallbackComponent } from './pages/auth-callback-component/auth-callback-component';

export const routes: Routes = [
  { path: '', redirectTo: 'login', pathMatch: 'full' },
  { path: 'login', component: LoginComponent },
  { path: 'auth/callback', component: AuthCallbackComponent },
  { path: 'home', component: HomeComponent },
  { path: 'events', component: EventsComponent },
  { path: 'events/create', component: CreateEventComponent },
  { path: 'events/:id', component: EventDetailComponent },
  { path: '**', redirectTo: 'login' }
];
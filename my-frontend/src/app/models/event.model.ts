export interface Event {
  id: number;
  organizer_id: number;
  organizer_name: string;
  title: string;
  description?: string;
  start_datetime: string;
  end_datetime: string;
  location?: string;
  participation_mode?: string;
  category?: string;
  faculty?: string;
  status: string;
  entry_type : string;
  registration_link?: string;
  max_participants?: number;
  registration_deadline?: string;
  created_at: string;
  updated_at: string;
  sponsors?: { name: string, logo_path?: string, website_url?: string }[];
}

export interface EventRegistration {
  id: number;
  event_id: number;
  user_id: number;
  status: string;
  qr_code_token?: string;
  checked_in: boolean;
  checked_in_at?: string;
  registered_at: string;
}

export interface EventFeedback {
  id: number;
  event_id: number;
  user_id: number;
  rating: number;
  comment?: string;
  created_at: string;
}

export interface EventMaterial {
  id: number;
  event_id: number;
  uploaded_by: number;
  file_name: string;
  file_type?: string;
  file_path: string;
  file_size_kb?: number;
  uploaded_at: string;
}

export interface EventSponsor {
  id: number;
  event_id: number;
  name: string;
  logo_path?: string;
  website_url?: string;
}
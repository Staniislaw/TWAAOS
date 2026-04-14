export interface User {
  id: number;
  full_name: string;
  email: string;
  role: string;
  oauth_provider?: string;
  is_active: boolean;
  created_at: string;
}
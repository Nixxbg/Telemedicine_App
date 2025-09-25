// User types
export interface User {
  id: string;
  email: string;
  user_type: 'patient' | 'doctor';
  is_active: boolean;
  created_at: string;
  updated_at: string;
  last_login?: string;
}

// Patient types  
export interface Patient {
  user_id: string;
  username: string;
  first_name: string;
  last_name: string;
  date_of_birth: string;
  phone_number?: string;
  emergency_contact?: EmergencyContact;
  profile_completed: boolean;
}

export interface PatientProfile extends Patient {
  user: User;
}

export interface EmergencyContact {
  name: string;
  phone: string;  
  relationship: string;
}

// Doctor types
export interface Doctor {
  user_id: string;
  doctor_id: string;
  first_name: string;
  last_name: string;
  specialization: string;
  license_number: string;
  years_experience?: number;
  is_available: boolean;
}

export interface DoctorProfile extends Doctor {
  user: User;
}

// Authentication types
export interface PatientRegistration {
  email: string;
  username: string;
  password: string;
  first_name: string;
  last_name: string;
  date_of_birth: string;
  phone_number?: string;
}

export interface PatientLogin {
  email: string;
  password: string;
}

export interface DoctorLogin {
  email: string;
  doctor_id: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user_type: 'patient' | 'doctor';
  profile: PatientProfile | DoctorProfile;
}

// Medical Record types
export interface MedicalRecord {
  id: string;
  patient_id: string;
  record_type: 'medication' | 'allergy' | 'procedure' | 'condition' | 'vaccine';
  title: string;
  description?: string;
  current_version: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  created_by: string;
  retention_weeks: number;
}

export interface MedicalRecordVersion {
  id: string;
  record_id: string;
  version_number: number;
  data: Record<string, any>;
  created_at: string;
  created_by: string;
  change_summary?: string;
}

// Appointment types
export interface Appointment {
  id: string;
  patient_id: string;
  doctor_id: string;
  scheduled_start: string;
  scheduled_end: string;
  status: 'scheduled' | 'confirmed' | 'in_progress' | 'completed' | 'cancelled' | 'no_show';
  consultation_type: 'initial' | 'follow_up' | 'urgent';
  notes?: string;
  created_at: string;
  updated_at: string;
}

// Message types
export interface Message {
  id: string;
  sender_id: string;
  recipient_id: string;
  content: string;
  message_type: 'text' | 'file' | 'appointment_update';
  appointment_id?: string;
  is_read: boolean;
  created_at: string;
}

// Questionnaire types
export interface QuestionnaireProgress {
  id: string;
  patient_id: string;
  questionnaire_type: 'medical_history' | 'symptoms' | 'lifestyle';
  responses: Record<string, any>;
  completion_percentage: number;
  is_completed: boolean;
  started_at: string;
  completed_at?: string;
}

// API Response types
export interface ApiResponse<T> {
  data: T;
  message?: string;
  errors?: Record<string, string[]>;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}
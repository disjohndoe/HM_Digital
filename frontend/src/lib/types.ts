export interface Tenant {
  id: string;
  naziv: string;
  vrsta: string;
  email: string;
  telefon: string | null;
  adresa: string | null;
  oib: string | null;
  grad: string | null;
  postanski_broj: string | null;
  zupanija: string | null;
  web: string | null;
  sifra_ustanove: string | null;
  oid: string | null;
  plan_tier: string;
  trial_expires_at: string | null;
  is_active: boolean;
  cezih_status: string;
}

export interface User {
  id: string;
  email: string;
  ime: string;
  prezime: string;
  titula: string | null;
  telefon: string | null;
  role: string;
  is_active: boolean;
  last_login_at: string | null;
  tenant_id: string;
  created_at: string;
  tenant?: Tenant;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User | null;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  naziv_klinike: string;
  vrsta: string;
  email: string;
  password: string;
  ime: string;
  prezime: string;
}

export interface UserCreate {
  email: string;
  password: string;
  ime: string;
  prezime: string;
  titula?: string;
  telefon?: string;
  role: string;
}

export interface Patient {
  id: string;
  ime: string;
  prezime: string;
  datum_rodjenja: string | null;
  spol: string | null;
  oib: string | null;
  mbo: string | null;
  adresa: string | null;
  grad: string | null;
  postanski_broj: string | null;
  telefon: string | null;
  mobitel: string | null;
  email: string | null;
  napomena: string | null;
  alergije: string | null;
  is_active: boolean;
  tenant_id: string;
  created_at: string;
  updated_at: string;
}

export interface PatientCreate {
  ime: string;
  prezime: string;
  datum_rodjenja?: string | null;
  spol?: string | null;
  oib?: string | null;
  mbo?: string | null;
  adresa?: string | null;
  grad?: string | null;
  postanski_broj?: string | null;
  telefon?: string | null;
  mobitel?: string | null;
  email?: string | null;
  napomena?: string | null;
  alergije?: string | null;
}

export interface PatientUpdate {
  ime?: string | null;
  prezime?: string | null;
  datum_rodjenja?: string | null;
  spol?: string | null;
  oib?: string | null;
  mbo?: string | null;
  adresa?: string | null;
  grad?: string | null;
  postanski_broj?: string | null;
  telefon?: string | null;
  mobitel?: string | null;
  email?: string | null;
  napomena?: string | null;
  alergije?: string | null;
  is_active?: boolean | null;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
}

export type AppointmentStatus = "zakazan" | "potvrdjen" | "u_tijeku" | "zavrsen" | "otkazan" | "nije_dosao";
export type AppointmentVrsta = "pregled" | "kontrola" | "lijecenje" | "higijena" | "konzultacija" | "hitno";

export interface Appointment {
  id: string;
  tenant_id: string;
  patient_id: string;
  doktor_id: string;
  datum_vrijeme: string;
  trajanje_minuta: number;
  status: AppointmentStatus;
  vrsta: AppointmentVrsta;
  napomena: string | null;
  patient_ime?: string | null;
  patient_prezime?: string | null;
  doktor_ime?: string | null;
  doktor_prezime?: string | null;
  created_at: string;
  updated_at: string;
}

export interface AppointmentCreate {
  patient_id: string;
  doktor_id: string;
  datum_vrijeme: string;
  trajanje_minuta?: number;
  vrsta?: string;
  napomena?: string;
}

export interface AvailableSlot {
  start: string;
  end: string;
}

// --- Procedures ---

export interface Procedure {
  id: string;
  sifra: string;
  naziv: string;
  opis: string | null;
  cijena_cents: number;
  trajanje_minuta: number;
  kategorija: string;
  is_active: boolean;
  tenant_id: string;
  created_at: string;
  updated_at: string;
}

export interface ProcedureCreate {
  sifra: string;
  naziv: string;
  opis?: string | null;
  cijena_cents?: number;
  trajanje_minuta?: number;
  kategorija: string;
}

export interface ProcedureUpdate {
  sifra?: string | null;
  naziv?: string | null;
  opis?: string | null;
  cijena_cents?: number | null;
  trajanje_minuta?: number | null;
  kategorija?: string | null;
  is_active?: boolean | null;
}

export interface PerformedProcedure {
  id: string;
  patient_id: string;
  appointment_id: string | null;
  procedure_id: string;
  doktor_id: string;
  lokacija: string | null;
  datum: string;
  cijena_cents: number;
  napomena: string | null;
  procedure_naziv: string | null;
  procedure_sifra: string | null;
  doktor_ime: string | null;
  doktor_prezime: string | null;
  tenant_id: string;
  created_at: string;
  updated_at: string;
}

export interface PerformedProcedureCreate {
  patient_id: string;
  procedure_id: string;
  appointment_id?: string | null;
  lokacija?: string | null;
  datum: string;
  cijena_cents?: number | null;
  napomena?: string | null;
}

// --- Medical Records ---

export type RecordTip =
  | "nalaz"
  | "dijagnoza"
  | "mišljenje"
  | "preporuka"
  | "epikriza"
  | "anamneza";

export interface MedicalRecord {
  id: string;
  patient_id: string;
  doktor_id: string;
  appointment_id: string | null;
  datum: string;
  tip: string;
  dijagnoza_mkb: string | null;
  dijagnoza_tekst: string | null;
  sadrzaj: string;
  cezih_sent: boolean;
  cezih_sent_at: string | null;
  cezih_reference_id: string | null;
  doktor_ime: string | null;
  doktor_prezime: string | null;
  tenant_id: string;
  created_at: string;
  updated_at: string;
}

export interface MedicalRecordCreate {
  patient_id: string;
  appointment_id?: string | null;
  datum: string;
  tip: string;
  dijagnoza_mkb?: string | null;
  dijagnoza_tekst?: string | null;
  sadrzaj: string;
}

export interface MedicalRecordUpdate {
  appointment_id?: string | null;
  datum?: string | null;
  tip?: string | null;
  dijagnoza_mkb?: string | null;
  dijagnoza_tekst?: string | null;
  sadrzaj?: string | null;
}

// --- Dashboard ---

export interface DashboardStats {
  danas_termini: number;
  ukupno_pacijenti: number;
  ovaj_tjedan_termini: number;
  novi_pacijenti_mjesec: number;
  cezih_status: string;
}

export interface TodayAppointment {
  id: string;
  patient_id: string;
  datum_vrijeme: string;
  trajanje_minuta: number;
  status: AppointmentStatus;
  vrsta: AppointmentVrsta;
  patient_ime: string | null;
  patient_prezime: string | null;
  doktor_ime: string | null;
  doktor_prezime: string | null;
}

// --- Documents ---

export interface Document {
  id: string;
  patient_id: string;
  naziv: string;
  kategorija: string;
  file_size: number;
  mime_type: string;
  uploaded_by: string;
  created_at: string;
}

export interface DocumentUploadResponse {
  id: string;
  patient_id: string;
  naziv: string;
  kategorija: string;
  file_size: number;
  mime_type: string;
  created_at: string;
}

// --- Plan Usage ---

export interface PlanUsage {
  plan_tier: string;
  users: { current: number; max: number };
  patients: { current: number; max: number | null };
  sessions: { current: number; max: number };
  cezih_access: boolean;
  trial_days_remaining: number | null;
}

// --- Agent ---

export interface AgentSecretResponse {
  agent_secret: string;
}

// --- CEZIH ---

export interface CezihStatusResponse {
  mock: boolean;
  connected: boolean;
  mode: string;
  agent_connected: boolean;
  last_heartbeat: string | null;
}

export interface InsuranceCheckResponse {
  mock: boolean;
  mbo: string;
  ime: string;
  prezime: string;
  datum_rodjenja: string;
  osiguravatelj: string;
  status_osiguranja: string;
  broj_osiguranja: string;
}

export interface ENalazResponse {
  mock: boolean;
  success: boolean;
  reference_id: string;
  sent_at: string;
}

export interface EUputnicaItem {
  mock: boolean;
  id: string;
  datum_izdavanja: string;
  izdavatelj: string;
  svrha: string;
  specijalist: string;
  status: string;
}

export interface EUputniceResponse {
  mock: boolean;
  items: EUputnicaItem[];
}

export interface EReceptLijekEntry {
  atk: string;
  naziv: string;
  kolicina: number;
  doziranje: string;
  napomena: string;
}

export interface EReceptResponse {
  mock: boolean;
  success: boolean;
  recept_id: string;
}

// --- CEZIH Activity Log ---

export interface CezihActivityItem {
  id: string;
  action: string;
  resource_id: string | null;
  details: string | null;
  created_at: string;
  user_id: string | null;
}

export interface CezihActivityListResponse {
  items: CezihActivityItem[];
  total: number;
}

// --- Patient CEZIH Summary ---

export interface PatientCezihInsurance {
  mbo: string | null;
  status_osiguranja: string | null;
  osiguravatelj: string | null;
  last_checked: string | null;
}

export interface PatientCezihENalaz {
  record_id: string;
  datum: string;
  tip: string;
  reference_id: string | null;
  cezih_sent_at: string | null;
}

export interface PatientCezihERecept {
  recept_id: string;
  datum: string;
  lijekovi: string[];
}

export interface PatientCezihSummary {
  mock: boolean;
  insurance: PatientCezihInsurance;
  e_nalaz_history: PatientCezihENalaz[];
  e_recept_history: PatientCezihERecept[];
}

// --- CEZIH Dashboard Stats ---

export interface CezihDashboardStats {
  mock: boolean;
  danas_operacije: number;
  otvorene_uputnice: number;
  zadnja_operacija: string | null;
}

// --- Drug Search ---

export interface LijekItem {
  atk: string;
  naziv: string;
  oblik: string;
  jacina: string;
}

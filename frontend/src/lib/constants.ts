export const SPOL_OPTIONS = [
  { value: "M", label: "Muški" },
  { value: "Z", label: "Ženski" },
] as const;

export const APPOINTMENT_STATUS: Record<string, string> = {
  zakazan: "Zakazan",
  potvrdjen: "Potvrđen",
  u_tijeku: "U tijeku",
  zavrsen: "Završen",
  otkazan: "Otkazan",
  nije_dosao: "Nije došao",
};

export const APPOINTMENT_VRSTA: Record<string, string> = {
  pregled: "Pregled",
  kontrola: "Kontrola",
  lijecenje: "Liječenje",
  higijena: "Higijena",
  dijagnostika: "Dijagnostika",
  intervencija: "Intervencija",
  kontrola_nalaza: "Kontrola nalaza",
  konzultacija: "Konzultacija",
  hitno: "Hitno",
};

export const APPOINTMENT_VRSTA_COLORS: Record<string, string> = {
  pregled: "bg-blue-100 border-blue-300 text-blue-900",
  kontrola: "bg-green-100 border-green-300 text-green-900",
  lijecenje: "bg-purple-100 border-purple-300 text-purple-900",
  higijena: "bg-pink-100 border-pink-300 text-pink-900",
  dijagnostika: "bg-cyan-100 border-cyan-300 text-cyan-900",
  intervencija: "bg-orange-100 border-orange-300 text-orange-900",
  kontrola_nalaza: "bg-teal-100 border-teal-300 text-teal-900",
  konzultacija: "bg-amber-100 border-amber-300 text-amber-900",
  hitno: "bg-red-100 border-red-300 text-red-900",
};

export const APPOINTMENT_STATUS_COLORS: Record<string, string> = {
  zakazan: "bg-slate-100 text-slate-700",
  potvrdjen: "bg-blue-100 text-blue-700",
  u_tijeku: "bg-yellow-100 text-yellow-700",
  zavrsen: "bg-green-100 text-green-700",
  otkazan: "bg-red-100 text-red-700",
  nije_dosao: "bg-orange-100 text-orange-700",
};

export const WORKING_HOURS_START = 8;
export const WORKING_HOURS_END = 20;
export const SLOT_GRANULARITY = 15;

export const DURATION_OPTIONS = [15, 30, 45, 60, 90, 120] as const;

// --- Procedures ---

export const PROCEDURE_KATEGORIJA: Record<string, string> = {
  dijagnostika: "Dijagnostika",
  pregled: "Pregled",
  kirurgija: "Kirurgija",
  terapija: "Terapija",
  rehabilitacija: "Rehabilitacija",
  prevencija: "Prevencija",
  estetika: "Estetske procedure",
  laboratorij: "Laboratorijske pretrage",
  pomocne: "Pomoćne procedure",
  ostalo: "Ostalo",
};

export const PROCEDURE_KATEGORIJA_OPTIONS = Object.entries(PROCEDURE_KATEGORIJA).map(
  ([value, label]) => ({ value, label })
);

// --- Medical Records ---

export const RECORD_TIP: Record<string, string> = {
  nalaz: "Nalaz",
  dijagnoza: "Dijagnoza",
  "mišljenje": "Mišljenje",
  preporuka: "Preporuka",
  epikriza: "Epikriza",
  anamneza: "Anamneza",
};

export const RECORD_TIP_OPTIONS = Object.entries(RECORD_TIP).map(
  ([value, label]) => ({ value, label })
);

export const RECORD_TIP_COLORS: Record<string, string> = {
  nalaz: "bg-blue-100 text-blue-800",
  dijagnoza: "bg-red-100 text-red-800",
  "mišljenje": "bg-purple-100 text-purple-800",
  preporuka: "bg-green-100 text-green-800",
  epikriza: "bg-amber-100 text-amber-800",
  anamneza: "bg-cyan-100 text-cyan-800",
};

// --- User Roles ---

export const USER_ROLE: Record<string, string> = {
  admin: "Administrator",
  doctor: "Liječnik",
  nurse: "Medicinska sestra",
  receptionist: "Recepcija",
};

export const USER_ROLE_OPTIONS = Object.entries(USER_ROLE).map(
  ([value, label]) => ({ value, label })
);

// --- Tenant ---

export const TENANT_VRSTA: Record<string, string> = {
  ordinacija: "Ordinacija",
  poliklinika: "Poliklinika",
  dom_zdravlja: "Dom zdravlja",
};

export const TENANT_VRSTA_OPTIONS = Object.entries(TENANT_VRSTA).map(
  ([value, label]) => ({ value, label })
);

export const PLAN_TIER: Record<string, string> = {
  trial: "Trial",
  solo: "Solo",
  poliklinika: "Poliklinika",
  poliklinika_plus: "Poliklinika+",
};

// --- CEZIH ---

export const CEZIH_STATUS: Record<string, string> = {
  nepovezano: "Nije povezano",
  u_pripremi: "U pripremi",
  testirano: "Testirano",
  certificirano: "Certificirano",
};

export const CEZIH_STATUS_COLORS: Record<string, string> = {
  nepovezano: "bg-muted",
  u_pripremi: "bg-yellow-400",
  testirano: "bg-blue-500",
  certificirano: "bg-green-500",
};

export const OSIGURANJE_STATUS: Record<string, { label: string; color: string }> = {
  Aktivan: { label: "Aktivan", color: "bg-green-100 text-green-800" },
  "Na čekanju": { label: "Na čekanju", color: "bg-yellow-100 text-yellow-800" },
  Neaktivan: { label: "Neaktivan", color: "bg-red-100 text-red-800" },
};

// --- CEZIH Activity ---

export const CEZIH_ACTION_LABELS: Record<string, string> = {
  insurance_check: "Provjera osiguranja",
  e_nalaz_send: "Slanje e-Nalaza",
  e_uputnica_retrieve: "Dohvat e-Uputnica",
  e_recept_send: "Slanje e-Recepta",
};

export const CEZIH_ACTION_COLORS: Record<string, string> = {
  insurance_check: "bg-blue-100 text-blue-800 border-blue-200",
  e_nalaz_send: "bg-green-100 text-green-800 border-green-200",
  e_uputnica_retrieve: "bg-purple-100 text-purple-800 border-purple-200",
  e_recept_send: "bg-orange-100 text-orange-800 border-orange-200",
};

// --- Documents ---

export const DOCUMENT_KATEGORIJA: Record<string, string> = {
  nalaz: "Nalaz",
  snimka: "Snimka",
  dokument: "Dokument",
  ostalo: "Ostalo",
};

export const DOCUMENT_KATEGORIJA_OPTIONS = Object.entries(DOCUMENT_KATEGORIJA).map(
  ([value, label]) => ({ value, label })
);

export const DOCUMENT_KATEGORIJA_COLORS: Record<string, string> = {
  nalaz: "bg-blue-100 text-blue-800",
  snimka: "bg-purple-100 text-purple-800",
  dokument: "bg-green-100 text-green-800",
  ostalo: "bg-gray-100 text-gray-800",
};

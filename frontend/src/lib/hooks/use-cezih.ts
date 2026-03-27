import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { api } from "@/lib/api-client"
import type {
  CezihActivityListResponse,
  CezihDashboardStats,
  CezihStatusResponse,
  ENalazResponse,
  EReceptResponse,
  EUputniceResponse,
  InsuranceCheckResponse,
  LijekItem,
  PatientCezihSummary,
} from "@/lib/types"

export function useCezihStatus() {
  return useQuery({
    queryKey: ["cezih", "status"],
    queryFn: () => api.get<CezihStatusResponse>("/cezih/status"),
  })
}

export function useInsuranceCheck() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (mbo: string) =>
      api.post<InsuranceCheckResponse>("/cezih/provjera-osiguranja", { mbo }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cezih", "activity"] })
      queryClient.invalidateQueries({ queryKey: ["cezih", "dashboard-stats"] })
    },
  })
}

export function useSendENalaz() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      patient_id,
      record_id,
      uputnica_id,
    }: {
      patient_id: string
      record_id: string
      uputnica_id?: string
    }) =>
      api.post<ENalazResponse>("/cezih/e-nalaz", { patient_id, record_id, uputnica_id }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["medical-records"] })
      queryClient.invalidateQueries({ queryKey: ["cezih", "euputnice"] })
      queryClient.invalidateQueries({ queryKey: ["cezih", "activity"] })
      queryClient.invalidateQueries({ queryKey: ["cezih", "dashboard-stats"] })
      queryClient.invalidateQueries({ queryKey: ["cezih", "patient"] })
    },
  })
}

export function useEUputnice() {
  return useQuery({
    queryKey: ["cezih", "euputnice"],
    queryFn: () => api.get<EUputniceResponse>("/cezih/e-uputnice"),
  })
}

export function useRetrieveEUputnice() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () =>
      api.post<EUputniceResponse>("/cezih/e-uputnica/preuzmi", {}),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cezih", "euputnice"] })
      queryClient.invalidateQueries({ queryKey: ["cezih", "activity"] })
      queryClient.invalidateQueries({ queryKey: ["cezih", "dashboard-stats"] })
    },
  })
}

export function useSendERecept() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ patient_id, lijekovi }: { patient_id: string; lijekovi: { atk: string; naziv: string; kolicina: number; doziranje: string; napomena: string }[] }) =>
      api.post<EReceptResponse>("/cezih/e-recept", { patient_id, lijekovi }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cezih", "activity"] })
      queryClient.invalidateQueries({ queryKey: ["cezih", "dashboard-stats"] })
      queryClient.invalidateQueries({ queryKey: ["cezih", "patient"] })
    },
  })
}

// --- Feature 1: Activity Log ---

export function useCezihActivity(limit: number = 20) {
  return useQuery({
    queryKey: ["cezih", "activity", limit],
    queryFn: () =>
      api.get<CezihActivityListResponse>(`/cezih/activity?limit=${limit}`),
  })
}

// --- Feature 2: Patient CEZIH Summary ---

export function usePatientCezihSummary(patientId: string) {
  return useQuery({
    queryKey: ["cezih", "patient", patientId],
    queryFn: () =>
      api.get<PatientCezihSummary>(`/cezih/patient/${patientId}/summary`),
    enabled: !!patientId,
  })
}

// --- Feature 3: Dashboard Stats ---

export function useCezihDashboardStats() {
  return useQuery({
    queryKey: ["cezih", "dashboard-stats"],
    queryFn: () => api.get<CezihDashboardStats>("/cezih/dashboard-stats"),
  })
}

// --- Feature 4: Drug Search ---

export function useDrugSearch(query: string) {
  return useQuery({
    queryKey: ["cezih", "lijekovi", query],
    queryFn: () =>
      api.get<LijekItem[]>(`/cezih/lijekovi?q=${encodeURIComponent(query)}`),
    enabled: query.length >= 2,
  })
}

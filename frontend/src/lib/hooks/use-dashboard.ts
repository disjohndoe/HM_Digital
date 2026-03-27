import { useQuery } from "@tanstack/react-query"

import { api } from "@/lib/api-client"
import type { DashboardStats, TodayAppointment } from "@/lib/types"

export function useDashboardStats() {
  return useQuery({
    queryKey: ["dashboard", "stats"],
    queryFn: () => api.get<DashboardStats>("/dashboard/stats"),
  })
}

export function useTodaySchedule() {
  return useQuery({
    queryKey: ["dashboard", "today"],
    queryFn: () => api.get<TodayAppointment[]>("/dashboard/today"),
  })
}

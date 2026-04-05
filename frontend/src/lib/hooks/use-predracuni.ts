import { useQuery } from "@tanstack/react-query"

import { api } from "@/lib/api-client"
import type { PaginatedResponse, Predracun } from "@/lib/types"

export function usePredracuni(patientId?: string) {
  return useQuery({
    queryKey: ["predracuni", patientId],
    queryFn: () =>
      api.get<PaginatedResponse<Predracun>>(
        `/predracuni?patient_id=${patientId}&limit=50`,
      ),
    enabled: !!patientId,
  })
}

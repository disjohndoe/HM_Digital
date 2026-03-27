import { useQuery, useQueryClient } from "@tanstack/react-query"

import { api } from "@/lib/api-client"

function blobQueryKey(documentId: string | null) {
  return ["document-blob", documentId] as const
}

export function useDocumentBlob(documentId: string | null) {
  const queryClient = useQueryClient()

  return useQuery({
    queryKey: blobQueryKey(documentId),
    queryFn: async () => {
      // Revoke any previously cached blob URL for this document before creating a new one
      const prev = queryClient.getQueryData<string>(blobQueryKey(documentId))
      if (prev) URL.revokeObjectURL(prev)

      const res = await api.fetchRaw(`/documents/${documentId}/download`)
      const blob = await res.blob()
      return URL.createObjectURL(blob)
    },
    enabled: !!documentId,
    staleTime: 5 * 60 * 1000,
    // Keep evicted entries only briefly — cleanup fires after gcTime
    gcTime: 30 * 1000,
    structuralSharing: false,
  })
}

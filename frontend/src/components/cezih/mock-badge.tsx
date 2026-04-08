"use client"

import { useMemo } from "react"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { useCezihStatus } from "@/lib/hooks/use-cezih"

/**
 * Shows a "DEMO" badge when CEZIH is running in mock mode.
 * Uses the already-cached useCezihStatus query — React Query deduplicates
 * by queryKey, so this doesn't create duplicate polling.
 */
export function MockBadge() {
  const { data } = useCezihStatus()
  const isDemo = data?.mock === true

  if (!isDemo) return null

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger>
          <span className="inline-flex items-center rounded-md bg-orange-100 px-2 py-0.5 text-xs font-medium text-orange-800 border border-orange-200">
            DEMO
          </span>
        </TooltipTrigger>
        <TooltipContent>
          <p className="max-w-[200px] text-xs">
            DEMO način rada — svi CEZIH podaci su simulirani. Prava CEZIH integracija
            zahtijeva lokalnog agenta, AKD karticu i certificirani VPN.
          </p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}

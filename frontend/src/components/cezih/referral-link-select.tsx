"use client"

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import type { EUputnicaItem } from "@/lib/types"

interface ReferralLinkSelectProps {
  value: string
  onChange: (value: string) => void
  referrals: EUputnicaItem[]
}

export function ReferralLinkSelect({ value, onChange, referrals }: ReferralLinkSelectProps) {
  const openReferrals = referrals.filter((r) => r.status === "Otvorena")

  if (openReferrals.length === 0) return null

  return (
    <div className="space-y-1">
      <label className="text-xs text-muted-foreground">Poveži s uputnicom</label>
      <Select value={value} onValueChange={(v) => onChange(v ?? "")}>
        <SelectTrigger className="h-8 text-xs">
          <SelectValue placeholder="Odaberi uputnicu (opcionalno)" />
        </SelectTrigger>
        <SelectContent className="min-w-[400px]">
          <SelectItem value="none">Bez uputnice</SelectItem>
          {openReferrals.map((ref) => (
            <SelectItem key={ref.id} value={ref.id}>
              {ref.id} — {ref.svrha}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  )
}

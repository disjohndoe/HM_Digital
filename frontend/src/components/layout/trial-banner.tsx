"use client"

import { useState } from "react"
import { Clock, X } from "lucide-react"
import { cn } from "@/lib/utils"
import { useAuth } from "@/lib/auth"

function formatTrialRemaining(days: number): string {
  if (days >= 1) {
    const d = Math.floor(days)
    return `${d} ${d === 1 ? "dan" : "dana"}`
  }
  const hours = Math.ceil(days * 24)
  return `${hours} ${hours === 1 ? "sat" : hours < 5 ? "sata" : "sati"}`
}

export function TrialBanner() {
  const { tenant } = useAuth()
  const [dismissed, setDismissed] = useState(
    () => typeof window !== "undefined" && sessionStorage.getItem("trial_banner_dismissed") === "1"
  )

  if (dismissed || !tenant || tenant.plan_tier !== "trial" || !tenant.trial_expires_at) {
    return null
  }

  const expiresAt = new Date(tenant.trial_expires_at)
  const now = new Date()
  const remainingMs = expiresAt.getTime() - now.getTime()
  if (remainingMs <= 0) return null

  const days = remainingMs / 86400000
  const isUrgent = days <= 3

  const handleDismiss = () => {
    setDismissed(true)
    sessionStorage.setItem("trial_banner_dismissed", "1")
  }

  return (
    <div
      className={cn(
        "flex items-center gap-3 px-4 py-2.5 text-sm border-b",
        isUrgent
          ? "bg-destructive/10 text-destructive border-destructive/20"
          : "bg-amber-50 text-amber-800 border-amber-200 dark:bg-amber-950/30 dark:text-amber-300 dark:border-amber-800/30"
      )}
    >
      <Clock className="h-4 w-4 shrink-0" />
      <span className="flex-1">
        {isUrgent
          ? `Vaš trial period ističe za ${formatTrialRemaining(days)}. Kontaktirajte nas na 097/7120-800.`
          : `Imate još ${formatTrialRemaining(days)} trial perioda.`}
      </span>
      <a
        href="https://hmdigital.hr/kontakt/"
        target="_blank"
        rel="noopener noreferrer"
        className="underline underline-offset-4 hover:opacity-80 shrink-0"
      >
        Kontaktirajte nas
      </a>
      <button onClick={handleDismiss} className="ml-1 hover:opacity-70 shrink-0">
        <X className="h-4 w-4" />
      </button>
    </div>
  )
}

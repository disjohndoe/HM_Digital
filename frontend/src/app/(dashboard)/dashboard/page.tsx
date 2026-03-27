"use client"

import { useAuth } from "@/lib/auth"
import { StatsCards } from "@/components/dashboard/stats-cards"
import { TodaySchedule } from "@/components/dashboard/today-schedule"
import { CezihDashboardWidgets } from "@/components/dashboard/cezih-widgets"

export default function DashboardPage() {
  const { user } = useAuth()

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">
          Dobrodošli, {user?.ime}!
        </h1>
        <p className="text-muted-foreground">
          Pregled vaše klinike za danas.
        </p>
      </div>

      <StatsCards />

      <CezihDashboardWidgets />

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="lg:col-span-2">
          <TodaySchedule />
        </div>
      </div>
    </div>
  )
}

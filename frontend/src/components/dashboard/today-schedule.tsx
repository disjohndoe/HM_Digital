"use client"

import Link from "next/link"
import { Clock, User } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { useTodaySchedule } from "@/lib/hooks/use-dashboard"
import { APPOINTMENT_STATUS, APPOINTMENT_STATUS_COLORS, APPOINTMENT_VRSTA, APPOINTMENT_VRSTA_COLORS } from "@/lib/constants"

export function TodaySchedule() {
  const { data: appointments, isLoading } = useTodaySchedule()

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Današnji raspored</CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-16 w-full" />
            ))}
          </div>
        ) : !appointments || appointments.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-8">
            <Clock className="h-8 w-8 text-muted-foreground mb-2" />
            <p className="text-sm text-muted-foreground">
              Nema zakazanih termina za danas
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            {appointments.map((apt) => {
              const time = new Date(apt.datum_vrijeme)
              const timeStr = time.toLocaleTimeString("hr-HR", {
                hour: "2-digit",
                minute: "2-digit",
              })
              const patientName = apt.patient_ime && apt.patient_prezime
                ? `${apt.patient_ime} ${apt.patient_prezime}`
                : "—"
              const doktorName = apt.doktor_ime && apt.doktor_prezime
                ? `${apt.doktor_ime} ${apt.doktor_prezime}`
                : ""

              return (
                <Link
                  key={apt.id}
                  href={`/termini`}
                  className="flex items-center gap-4 rounded-lg border p-3 hover:bg-accent/50 transition-colors"
                >
                  <div className="text-sm font-mono font-medium min-w-[56px]">
                    {timeStr}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <User className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                      <span className="text-sm font-medium truncate">
                        {patientName}
                      </span>
                    </div>
                    {doktorName && (
                      <p className="text-xs text-muted-foreground ml-[22px]">
                        {doktorName}
                      </p>
                    )}
                  </div>
                  <Badge
                    variant="outline"
                    className={APPOINTMENT_VRSTA_COLORS[apt.vrsta] ?? ""}
                  >
                    {APPOINTMENT_VRSTA[apt.vrsta] ?? apt.vrsta}
                  </Badge>
                  <Badge
                    variant="outline"
                    className={APPOINTMENT_STATUS_COLORS[apt.status] ?? ""}
                  >
                    {APPOINTMENT_STATUS[apt.status] ?? apt.status}
                  </Badge>
                </Link>
              )
            })}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

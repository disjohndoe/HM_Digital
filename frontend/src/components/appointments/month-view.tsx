"use client"

import { useMemo } from "react"
import { cn } from "@/lib/utils"
import { useAppointments } from "@/lib/hooks/use-appointments"
import { APPOINTMENT_VRSTA_COLORS } from "@/lib/constants"
import type { Appointment } from "@/lib/types"

interface MonthViewProps {
  selectedDate: Date
  doktorId?: string
  onDayClick: (date: Date) => void
  onAppointmentClick: (appointment: Appointment) => void
}

function formatDateKey(d: Date): string {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, "0")
  const day = String(d.getDate()).padStart(2, "0")
  return `${y}-${m}-${day}`
}

const DAY_NAMES = ["Pon", "Uto", "Sri", "Čet", "Pet", "Sub", "Ned"]

export function MonthView({ selectedDate, doktorId, onDayClick, onAppointmentClick }: MonthViewProps) {
  const year = selectedDate.getFullYear()
  const month = selectedDate.getMonth()

  // Build grid: 6 rows x 7 cols covering the month
  const calendarDays = useMemo(() => {
    const firstOfMonth = new Date(year, month, 1)
    // Monday = 0, Sunday = 6
    let startDay = firstOfMonth.getDay() - 1
    if (startDay < 0) startDay = 6

    const gridStart = new Date(year, month, 1 - startDay)
    const days: Date[] = []
    for (let i = 0; i < 42; i++) {
      const d = new Date(gridStart)
      d.setDate(d.getDate() + i)
      days.push(d)
    }
    return days
  }, [year, month])

  const dateFrom = formatDateKey(calendarDays[0])
  const dateTo = formatDateKey(calendarDays[calendarDays.length - 1])

  const { data } = useAppointments(dateFrom, dateTo, doktorId, undefined, 0, 200)

  const groupedByDay = useMemo(() => {
    const grouped: Record<string, Appointment[]> = {}
    if (data?.items) {
      for (const apt of data.items) {
        const key = formatDateKey(new Date(apt.datum_vrijeme))
        if (!grouped[key]) grouped[key] = []
        grouped[key].push(apt)
      }
    }
    return grouped
  }, [data])

  const today = formatDateKey(new Date())

  return (
    <div className="border rounded-lg bg-background overflow-hidden">
      {/* Day name headers */}
      <div className="grid grid-cols-7 border-b">
        {DAY_NAMES.map((name) => (
          <div key={name} className="py-2 text-center text-xs font-medium text-muted-foreground border-r last:border-r-0">
            {name}
          </div>
        ))}
      </div>

      {/* Day cells — 6 rows */}
      <div className="grid grid-cols-7">
        {calendarDays.map((day, i) => {
          const key = formatDateKey(day)
          const isCurrentMonth = day.getMonth() === month
          const isToday = key === today
          const appointments = groupedByDay[key] ?? []

          return (
            <div
              key={key}
              className={cn(
                "min-h-[100px] border-r border-b last:border-r-0 p-1.5 cursor-pointer transition-colors hover:bg-accent/50",
                !isCurrentMonth && "bg-muted/30",
                i % 7 === 5 || i % 7 === 6 ? "bg-muted/10" : "",
              )}
              onClick={() => onDayClick(day)}
            >
              {/* Day number */}
              <div className="flex items-center justify-between mb-1">
                <span
                  className={cn(
                    "text-xs font-medium w-6 h-6 flex items-center justify-center rounded-full",
                    isToday && "bg-primary text-primary-foreground",
                    !isCurrentMonth && "text-muted-foreground/50",
                  )}
                >
                  {day.getDate()}
                </span>
                {appointments.length > 0 && (
                  <span className="text-[10px] text-muted-foreground">{appointments.length}</span>
                )}
              </div>

              {/* Appointment previews (max 3) */}
              <div className="space-y-0.5">
                {appointments.slice(0, 3).map((apt) => {
                  const start = new Date(apt.datum_vrijeme)
                  const time = `${String(start.getHours()).padStart(2, "0")}:${String(start.getMinutes()).padStart(2, "0")}`
                  const name = apt.patient_prezime || "—"
                  return (
                    <div
                      key={apt.id}
                      className={cn(
                        "text-[10px] leading-tight px-1 py-0.5 rounded truncate cursor-pointer",
                        APPOINTMENT_VRSTA_COLORS[apt.vrsta] ?? "bg-gray-100 border-gray-300",
                      )}
                      onClick={(e) => {
                        e.stopPropagation()
                        onAppointmentClick(apt)
                      }}
                    >
                      {time} {name}
                    </div>
                  )
                })}
                {appointments.length > 3 && (
                  <div className="text-[10px] text-muted-foreground pl-1">
                    +{appointments.length - 3} više
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

"use client"

import { WORKING_HOURS_START, WORKING_HOURS_END, SLOT_GRANULARITY } from "@/lib/constants"
import type { Appointment } from "@/lib/types"
import { TimeSlot } from "./time-slot"
import { AppointmentCard } from "./appointment-card"

interface DayColumnProps {
  date: Date
  appointments: Appointment[]
  onSlotClick: (date: Date) => void
  onAppointmentClick: (appointment: Appointment) => void
}

export function DayColumn({ date, appointments, onSlotClick, onAppointmentClick }: DayColumnProps) {
  const hours: number[] = []
  for (let h = WORKING_HOURS_START; h < WORKING_HOURS_END; h++) {
    hours.push(h)
  }

  const slotsPerHour = 60 / SLOT_GRANULARITY
  const rowHeight = 16 // px per 15-min row

  const dayLabel = date.toLocaleDateString("hr-HR", {
    weekday: "short",
    day: "numeric",
    month: "numeric",
  })

  return (
    <div className="flex-1 min-w-0 border-l border-border">
      {/* Day header */}
      <div className="h-12 flex items-center justify-center text-xs font-medium text-muted-foreground border-b border-border">
        {dayLabel}
      </div>

      <div className="relative">
        {/* Hour labels + grid */}
        {hours.map((hour) => (
          <div key={hour} className="flex">
            {/* Hour label */}
            <div className="w-14 shrink-0 text-[10px] text-muted-foreground pr-2 pt-0 text-right">
              {String(hour).padStart(2, "0")}:00
            </div>
            {/* Rows */}
            <div className="flex-1 relative border-l border-border/50">
              {Array.from({ length: slotsPerHour }).map((_, i) => (
                <TimeSlot
                  key={`${hour}-${i}`}
                  hour={hour}
                  minute={i * SLOT_GRANULARITY}
                  onClick={(d) => {
                    // Adjust the date to match the column date
                    const clicked = new Date(date)
                    clicked.setHours(d.getHours(), d.getMinutes(), 0, 0)
                    onSlotClick(clicked)
                  }}
                />
              ))}
            </div>
          </div>
        ))}

        {/* Appointment cards overlay */}
        <div
          className="absolute top-0 left-14 right-0"
          style={{ height: `${(WORKING_HOURS_END - WORKING_HOURS_START) * slotsPerHour * rowHeight}px` }}
        >
          {appointments.map((apt) => (
            <AppointmentCard
              key={apt.id}
              appointment={apt}
              onClick={onAppointmentClick}
            />
          ))}
        </div>
      </div>
    </div>
  )
}

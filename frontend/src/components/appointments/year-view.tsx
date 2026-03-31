"use client"

import { useMemo } from "react"
import { cn } from "@/lib/utils"
import { useAppointments } from "@/lib/hooks/use-appointments"

interface YearViewProps {
  selectedDate: Date
  doktorId?: string
  onMonthClick: (date: Date) => void
}

function formatDateKey(d: Date): string {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, "0")
  const day = String(d.getDate()).padStart(2, "0")
  return `${y}-${m}-${day}`
}

const MONTH_NAMES = [
  "Siječanj", "Veljača", "Ožujak", "Travanj", "Svibanj", "Lipanj",
  "Srpanj", "Kolovoz", "Rujan", "Listopad", "Studeni", "Prosinac",
]

const DAY_INITIALS = ["P", "U", "S", "Č", "P", "S", "N"]

export function YearView({ selectedDate, doktorId, onMonthClick }: YearViewProps) {
  const year = selectedDate.getFullYear()

  const dateFrom = `${year}-01-01`
  const dateTo = `${year}-12-31`

  const { data } = useAppointments(dateFrom, dateTo, doktorId, undefined, 0, 200)

  const countByDay = useMemo(() => {
    const counts: Record<string, number> = {}
    if (data?.items) {
      for (const apt of data.items) {
        const key = formatDateKey(new Date(apt.datum_vrijeme))
        counts[key] = (counts[key] || 0) + 1
      }
    }
    return counts
  }, [data])

  const today = formatDateKey(new Date())

  return (
    <div className="border rounded-lg bg-background p-4">
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
        {Array.from({ length: 12 }).map((_, monthIdx) => (
          <MiniMonth
            key={monthIdx}
            year={year}
            month={monthIdx}
            countByDay={countByDay}
            today={today}
            onClick={() => onMonthClick(new Date(year, monthIdx, 1))}
          />
        ))}
      </div>
    </div>
  )
}

function MiniMonth({
  year,
  month,
  countByDay,
  today,
  onClick,
}: {
  year: number
  month: number
  countByDay: Record<string, number>
  today: string
  onClick: () => void
}) {
  const calendarDays = useMemo(() => {
    const firstOfMonth = new Date(year, month, 1)
    let startDay = firstOfMonth.getDay() - 1
    if (startDay < 0) startDay = 6
    const daysInMonth = new Date(year, month + 1, 0).getDate()

    const cells: (number | null)[] = []
    for (let i = 0; i < startDay; i++) cells.push(null)
    for (let d = 1; d <= daysInMonth; d++) cells.push(d)
    while (cells.length < 42) cells.push(null)
    return cells
  }, [year, month])

  // Count total appointments for this month
  const monthTotal = useMemo(() => {
    let total = 0
    const daysInMonth = new Date(year, month + 1, 0).getDate()
    for (let d = 1; d <= daysInMonth; d++) {
      const key = `${year}-${String(month + 1).padStart(2, "0")}-${String(d).padStart(2, "0")}`
      total += countByDay[key] || 0
    }
    return total
  }, [year, month, countByDay])

  return (
    <div
      className="cursor-pointer hover:bg-accent/30 rounded-lg p-2 transition-colors"
      onClick={onClick}
    >
      {/* Month header */}
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium">{MONTH_NAMES[month]}</span>
        {monthTotal > 0 && (
          <span className="text-[10px] text-muted-foreground bg-muted px-1.5 py-0.5 rounded-full">
            {monthTotal}
          </span>
        )}
      </div>

      {/* Day initials */}
      <div className="grid grid-cols-7 gap-0">
        {DAY_INITIALS.map((d, i) => (
          <div key={i} className="text-[9px] text-center text-muted-foreground pb-0.5">
            {d}
          </div>
        ))}
      </div>

      {/* Day cells */}
      <div className="grid grid-cols-7 gap-0">
        {calendarDays.map((day, i) => {
          if (day === null) {
            return <div key={`e-${i}`} className="h-5" />
          }
          const key = `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`
          const count = countByDay[key] || 0
          const isToday = key === today

          return (
            <div
              key={key}
              className={cn(
                "h-5 flex items-center justify-center text-[10px] rounded-sm",
                isToday && "ring-1 ring-primary font-bold",
                count === 0 && "text-muted-foreground",
                count > 0 && count <= 2 && "bg-blue-100 text-blue-800",
                count > 2 && count <= 5 && "bg-blue-200 text-blue-900",
                count > 5 && "bg-blue-400 text-white",
              )}
            >
              {day}
            </div>
          )
        })}
      </div>
    </div>
  )
}

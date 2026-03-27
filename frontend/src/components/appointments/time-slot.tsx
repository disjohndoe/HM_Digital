"use client"

interface TimeSlotProps {
  hour: number
  minute: number
  onClick: (date: Date) => void
}

export function TimeSlot({ hour, minute, onClick }: TimeSlotProps) {
  const now = new Date()
  const slotDate = new Date(now)
  slotDate.setHours(hour, minute, 0, 0)

  return (
    <div
      className="h-4 border-b border-r border-border/50 hover:bg-primary/5 cursor-pointer transition-colors"
      onClick={() => onClick(slotDate)}
      title={`${String(hour).padStart(2, "0")}:${String(minute).padStart(2, "0")}`}
    />
  )
}

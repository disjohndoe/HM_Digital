"use client"

import { useState, useCallback } from "react"
import { PlusIcon, ChevronLeftIcon, ChevronRightIcon, CalendarIcon } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { PageHeader } from "@/components/shared/page-header"
import { CalendarView } from "@/components/appointments/calendar-view"
import { AppointmentForm } from "@/components/appointments/appointment-form"
import { AppointmentDetail } from "@/components/appointments/appointment-detail"
import { useDoctors } from "@/lib/hooks/use-appointments"
import type { Appointment } from "@/lib/types"

export default function TerminiPage() {
  const [selectedDate, setSelectedDate] = useState(() => {
    const now = new Date()
    now.setHours(0, 0, 0, 0)
    return now
  })
  const [viewMode, setViewMode] = useState<"day" | "week">("day")
  const [doktorId, setDoktorId] = useState<string>("")

  const [formOpen, setFormOpen] = useState(false)
  const [detailOpen, setDetailOpen] = useState(false)
  const [selectedAppointment, setSelectedAppointment] = useState<Appointment | null>(null)
  const [defaultSlotDate, setDefaultSlotDate] = useState<Date | undefined>()

  const { data: doctorsData } = useDoctors()
  const doctors = doctorsData ?? []

  const navigateDate = useCallback((days: number) => {
    setSelectedDate((prev) => {
      const next = new Date(prev)
      next.setDate(next.getDate() + days)
      return next
    })
  }, [])

  const goToToday = useCallback(() => {
    const now = new Date()
    now.setHours(0, 0, 0, 0)
    setSelectedDate(now)
  }, [])

  function handleSlotClick(date: Date) {
    setDefaultSlotDate(date)
    setSelectedAppointment(null)
    setFormOpen(true)
  }

  function handleAppointmentClick(apt: Appointment) {
    setSelectedAppointment(apt)
    setDetailOpen(true)
  }

  function handleEditAppointment(apt: Appointment) {
    setSelectedAppointment(apt)
    setDefaultSlotDate(new Date(apt.datum_vrijeme))
    setFormOpen(true)
  }

  function handleNewAppointment() {
    setDefaultSlotDate(selectedDate)
    setSelectedAppointment(null)
    setFormOpen(true)
  }

  return (
    <div className="space-y-4">
      <PageHeader title="Termini" description="Kalendar termina">
        <Button onClick={handleNewAppointment}>
          <PlusIcon className="mr-2 h-4 w-4" />
          Novi termin
        </Button>
      </PageHeader>

      {/* Toolbar */}
      <div className="flex flex-wrap items-center gap-2">
        <Button variant="outline" size="sm" onClick={() => navigateDate(-1)}>
          <ChevronLeftIcon className="h-4 w-4" />
        </Button>
        <Button variant="outline" size="sm" onClick={goToToday}>
          <CalendarIcon className="mr-1 h-4 w-4" />
          Danas
        </Button>
        <Button variant="outline" size="sm" onClick={() => navigateDate(1)}>
          <ChevronRightIcon className="h-4 w-4" />
        </Button>

        <span className="text-sm font-medium ml-2">
          {selectedDate.toLocaleDateString("hr-HR", {
            weekday: "long",
            day: "numeric",
            month: "long",
            year: "numeric",
          })}
        </span>

        <div className="ml-auto flex items-center gap-2">
          {doctors.length > 1 && (
            <Select value={doktorId} onValueChange={(v) => setDoktorId(v ?? "")}>
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder="Svi doktori" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">Svi doktori</SelectItem>
                {doctors.map((d) => (
                  <SelectItem key={d.id} value={d.id}>
                    {d.prezime} {d.ime}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}

          <Select value={viewMode} onValueChange={(v) => setViewMode((v ?? "day") as "day" | "week")}>
            <SelectTrigger className="w-[100px]">
              <SelectValue>{viewMode === "day" ? "Dan" : "Tjedan"}</SelectValue>
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="day">Dan</SelectItem>
              <SelectItem value="week">Tjedan</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Calendar */}
      <CalendarView
        selectedDate={selectedDate}
        viewMode={viewMode}
        doktorId={doktorId || undefined}
        onSlotClick={handleSlotClick}
        onAppointmentClick={handleAppointmentClick}
      />

      {/* Dialogs */}
      <AppointmentForm
        open={formOpen}
        onOpenChange={setFormOpen}
        appointment={selectedAppointment ?? undefined}
        defaultDate={defaultSlotDate}
        defaultDoktorId={doktorId || undefined}
      />

      <AppointmentDetail
        appointment={selectedAppointment}
        open={detailOpen}
        onOpenChange={setDetailOpen}
        onEdit={handleEditAppointment}
        onUpdated={setSelectedAppointment}
      />
    </div>
  )
}

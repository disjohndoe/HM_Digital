"use client"

import { toast } from "sonner"
import { formatDateTimeHR } from "@/lib/utils"
import { APPOINTMENT_STATUS, APPOINTMENT_VRSTA, APPOINTMENT_STATUS_COLORS } from "@/lib/constants"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { useUpdateAppointment } from "@/lib/hooks/use-appointments"
import type { Appointment } from "@/lib/types"

interface AppointmentDetailProps {
  appointment: Appointment | null
  open: boolean
  onOpenChange: (open: boolean) => void
  onEdit: (appointment: Appointment) => void
  onUpdated?: (appointment: Appointment) => void
}

const QUICK_STATUS_ACTIONS: Record<string, { label: string; status: string }> = {
  zakazan: { label: "Potvrdi", status: "potvrdjen" },
  potvrdjen: { label: "Započni", status: "u_tijeku" },
  u_tijeku: { label: "Završi", status: "zavrsen" },
}

export function AppointmentDetail({ appointment, open, onOpenChange, onEdit, onUpdated }: AppointmentDetailProps) {
  const updateMutation = useUpdateAppointment()

  if (!appointment) return null

  const patientName = appointment.patient_ime && appointment.patient_prezime
    ? `${appointment.patient_ime} ${appointment.patient_prezime}`
    : "—"

  const doktorName = appointment.doktor_ime && appointment.doktor_prezime
    ? `${appointment.doktor_ime} ${appointment.doktor_prezime}`
    : "—"

  const appointmentId = appointment.id

  async function handleStatusChange(newStatus: string) {
    try {
      const updated = await updateMutation.mutateAsync({ id: appointmentId, data: { status: newStatus } })
      toast.success(`Status promijenjen: ${APPOINTMENT_STATUS[newStatus]}`)
      onUpdated?.(updated)
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Greška pri promjeni statusa")
    }
  }

  async function handleCancel() {
    try {
      const updated = await updateMutation.mutateAsync({ id: appointmentId, data: { status: "otkazan" } })
      toast.success("Termin otkazan")
      onUpdated?.(updated)
      onOpenChange(false)
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Greška pri otkazivanju")
    }
  }

  const quickAction = QUICK_STATUS_ACTIONS[appointment.status]

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Detalji termina</DialogTitle>
          <DialogDescription>
            {APPOINTMENT_VRSTA[appointment.vrsta] ?? appointment.vrsta}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Status */}
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Status</span>
            <Badge className={APPOINTMENT_STATUS_COLORS[appointment.status] ?? ""}>
              {APPOINTMENT_STATUS[appointment.status] ?? appointment.status}
            </Badge>
          </div>

          {/* Pacijent */}
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Pacijent</span>
            <span className="text-sm font-medium">{patientName}</span>
          </div>

          {/* Doktor */}
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Doktor</span>
            <span className="text-sm font-medium">{doktorName}</span>
          </div>

          {/* Datum */}
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Datum</span>
            <span className="text-sm font-medium">{formatDateTimeHR(appointment.datum_vrijeme)}</span>
          </div>

          {/* Trajanje */}
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Trajanje</span>
            <span className="text-sm font-medium">{appointment.trajanje_minuta} min</span>
          </div>

          {/* Napomena */}
          {appointment.napomena && (
            <div className="space-y-1">
              <span className="text-sm text-muted-foreground">Napomena</span>
              <p className="text-sm bg-muted rounded-md p-2">{appointment.napomena}</p>
            </div>
          )}

          {/* Actions */}
          <div className="flex flex-wrap gap-2 pt-2">
            {quickAction && (
              <Button
                size="sm"
                onClick={() => handleStatusChange(quickAction.status)}
                disabled={updateMutation.isPending}
              >
                {quickAction.label}
              </Button>
            )}
            {appointment.status === "zakazan" || appointment.status === "potvrdjen" ? (
              <Button size="sm" variant="destructive" onClick={handleCancel} disabled={updateMutation.isPending}>
                Otkaži
              </Button>
            ) : null}
            {(appointment.status === "zakazan" || appointment.status === "potvrdjen") && (
              <Button size="sm" variant="outline" onClick={() => { onOpenChange(false); onEdit(appointment) }}>
                Uredi
              </Button>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}

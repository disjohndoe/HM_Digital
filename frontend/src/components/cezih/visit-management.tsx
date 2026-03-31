"use client"

import { useState } from "react"
import { Calendar, Clock, Play, Square, RotateCcw, Trash2, Loader2 } from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  useCreateVisit,
  useCloseVisit,
  useReopenVisit,
  useCancelVisit,
} from "@/lib/hooks/use-cezih"
import { MockBadge } from "./mock-badge"

const ADMISSION_TYPES = [
  { code: "1", label: "Dnevna bolnica" },
  { code: "2", label: "Hitan prijem" },
  { code: "3", label: "Premještaj" },
  { code: "9", label: "Interna uputnica" },
]

const STATUS_COLORS: Record<string, string> = {
  "in-progress": "bg-blue-100 text-blue-800",
  finished: "bg-green-100 text-green-800",
  "entered-in-error": "bg-red-100 text-red-800",
}

const STATUS_LABELS: Record<string, string> = {
  "in-progress": "U tijeku",
  finished: "Završena",
  "entered-in-error": "Stornirana",
}

interface Visit {
  visit_id: string
  status: string
  period_start?: string
  period_end?: string
  admission_type?: string
}

interface VisitManagementProps {
  patientId: string
  patientMbo: string
}

export function VisitManagement({ patientId, patientMbo }: VisitManagementProps) {
  const [createOpen, setCreateOpen] = useState(false)
  const [admissionType, setAdmissionType] = useState("9")
  const [visits, setVisits] = useState<Visit[]>([])

  const createVisit = useCreateVisit()
  const closeVisit = useCloseVisit()
  const reopenVisit = useReopenVisit()
  const cancelVisit = useCancelVisit()

  const handleCreate = () => {
    const now = new Date().toISOString()
    createVisit.mutate(
      {
        patient_id: patientId,
        patient_mbo: patientMbo,
        period_start: now,
        admission_type_code: admissionType,
      },
      {
        onSuccess: (data) => {
          toast.success("Posjeta kreirana")
          setVisits((prev) => [
            {
              visit_id: data.visit_id,
              status: "in-progress",
              period_start: now,
              admission_type: admissionType,
            },
            ...prev,
          ])
          setCreateOpen(false)
        },
        onError: (err) => toast.error(err.message),
      }
    )
  }

  const handleClose = (visitId: string) => {
    const now = new Date().toISOString()
    closeVisit.mutate(
      { visitId, period_end: now },
      {
        onSuccess: () => {
          toast.success("Posjeta zatvorena")
          setVisits((prev) =>
            prev.map((v) =>
              v.visit_id === visitId ? { ...v, status: "finished", period_end: now } : v
            )
          )
        },
        onError: (err) => toast.error(err.message),
      }
    )
  }

  const handleReopen = (visitId: string) => {
    reopenVisit.mutate(visitId, {
      onSuccess: () => {
        toast.success("Posjeta ponovno otvorena")
        setVisits((prev) =>
          prev.map((v) =>
            v.visit_id === visitId ? { ...v, status: "in-progress", period_end: undefined } : v
          )
        )
      },
      onError: (err) => toast.error(err.message),
    })
  }

  const handleCancel = (visitId: string) => {
    cancelVisit.mutate(visitId, {
      onSuccess: () => {
        toast.success("Posjeta stornirana")
        setVisits((prev) =>
          prev.map((v) =>
            v.visit_id === visitId ? { ...v, status: "entered-in-error" } : v
          )
        )
      },
      onError: (err) => toast.error(err.message),
    })
  }

  const isPending =
    createVisit.isPending || closeVisit.isPending || reopenVisit.isPending || cancelVisit.isPending

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-lg flex items-center gap-2">
          <Calendar className="h-5 w-5" />
          Upravljanje posjetama
        </CardTitle>
        <div className="flex items-center gap-2">
          <MockBadge />
          <Dialog open={createOpen} onOpenChange={setCreateOpen}>
            <DialogTrigger render={<Button size="sm" disabled={!patientMbo} />}>
              <Play className="h-4 w-4 mr-1" />
              Nova posjeta
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Kreiranje nove posjete</DialogTitle>
              </DialogHeader>
              <div className="space-y-4 pt-2">
                <div>
                  <Label>Pacijent MBO</Label>
                  <Input value={patientMbo} disabled />
                </div>
                <div>
                  <Label>Način prijema</Label>
                  <Select value={admissionType} onValueChange={(v) => v && setAdmissionType(v)}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {ADMISSION_TYPES.map((t) => (
                        <SelectItem key={t.code} value={t.code}>
                          {t.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <Button
                  className="w-full"
                  onClick={handleCreate}
                  disabled={createVisit.isPending}
                >
                  {createVisit.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                  Kreiraj posjetu
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </CardHeader>
      <CardContent>
        {visits.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center py-4">
            Nema aktivnih posjeta. Kliknite &quot;Nova posjeta&quot; za kreiranje.
          </p>
        ) : (
          <div className="space-y-3">
            {visits.map((visit) => (
              <div
                key={visit.visit_id}
                className="flex items-center justify-between p-3 rounded-lg border"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <Badge className={STATUS_COLORS[visit.status] || "bg-gray-100"}>
                      {STATUS_LABELS[visit.status] || visit.status}
                    </Badge>
                    <span className="text-xs text-muted-foreground font-mono">
                      {visit.visit_id}
                    </span>
                  </div>
                  <div className="flex items-center gap-4 text-xs text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {visit.period_start
                        ? new Date(visit.period_start).toLocaleString("hr-HR")
                        : "—"}
                    </span>
                    {visit.period_end && (
                      <span>
                        → {new Date(visit.period_end).toLocaleString("hr-HR")}
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex gap-1">
                  {visit.status === "in-progress" && (
                    <>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleClose(visit.visit_id)}
                        disabled={isPending}
                        title="Zatvori posjetu"
                      >
                        <Square className="h-3 w-3" />
                      </Button>
                      <Button
                        size="sm"
                        variant="destructive"
                        onClick={() => handleCancel(visit.visit_id)}
                        disabled={isPending}
                        title="Storno"
                      >
                        <Trash2 className="h-3 w-3" />
                      </Button>
                    </>
                  )}
                  {visit.status === "finished" && (
                    <>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleReopen(visit.visit_id)}
                        disabled={isPending}
                        title="Ponovno otvori"
                      >
                        <RotateCcw className="h-3 w-3" />
                      </Button>
                      <Button
                        size="sm"
                        variant="destructive"
                        onClick={() => handleCancel(visit.visit_id)}
                        disabled={isPending}
                        title="Storno"
                      >
                        <Trash2 className="h-3 w-3" />
                      </Button>
                    </>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

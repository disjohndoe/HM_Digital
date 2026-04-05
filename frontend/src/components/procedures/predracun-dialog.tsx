"use client"

import { useState } from "react"
import { toast } from "sonner"
import { FileTextIcon } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { api } from "@/lib/api-client"
import { formatDateHR, formatCurrencyEUR } from "@/lib/utils"
import type { PerformedProcedure } from "@/lib/types"

interface PredracunDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  patientId: string
  selectedProcedures: PerformedProcedure[]
  onSuccess: () => void
}

export function PredracunDialog({
  open,
  onOpenChange,
  patientId,
  selectedProcedures,
  onSuccess,
}: PredracunDialogProps) {
  const [napomena, setNapomena] = useState("")
  const [loading, setLoading] = useState(false)

  const total = selectedProcedures.reduce((sum, p) => sum + p.cijena_cents, 0)

  async function handleGenerate() {
    setLoading(true)
    try {
      const res = await api.postRaw("/predracuni", {
        patient_id: patientId,
        performed_procedure_ids: selectedProcedures.map((p) => p.id),
        napomena: napomena || undefined,
      })

      const blob = await res.blob()
      const disposition = res.headers.get("content-disposition") || ""
      const match = disposition.match(/filename="?([^"]+)"?/)
      const filename = match ? match[1] : `predracun.pdf`

      const url = URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = filename
      a.click()
      URL.revokeObjectURL(url)

      toast.success("Predračun generiran")
      setNapomena("")
      onOpenChange(false)
      onSuccess()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Greška pri generiranju predračuna")
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FileTextIcon className="h-5 w-5" />
            Generiraj predračun
          </DialogTitle>
          <DialogDescription>
            Pregledajte odabrane postupke i generirajte predračun za pacijenta
          </DialogDescription>
        </DialogHeader>

        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Šifra</TableHead>
              <TableHead>Naziv</TableHead>
              <TableHead>Datum</TableHead>
              <TableHead className="text-right">Cijena</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {selectedProcedures.map((p) => (
              <TableRow key={p.id}>
                <TableCell className="font-mono text-xs text-muted-foreground">
                  {p.procedure_sifra}
                </TableCell>
                <TableCell className="font-medium">{p.procedure_naziv}</TableCell>
                <TableCell>{formatDateHR(p.datum)}</TableCell>
                <TableCell className="text-right">
                  {formatCurrencyEUR(p.cijena_cents / 100)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>

        <div className="flex justify-end border-t pt-2">
          <p className="text-lg font-bold">
            Ukupno: {formatCurrencyEUR(total / 100)}
          </p>
        </div>

        <div className="space-y-2">
          <Label htmlFor="napomena">Napomena (opcionalno)</Label>
          <Textarea
            id="napomena"
            placeholder="Dodatne napomene na predračunu..."
            value={napomena}
            onChange={(e) => setNapomena(e.target.value)}
          />
        </div>

        <div className="flex justify-end gap-2 pt-2">
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={loading}>
            Odustani
          </Button>
          <Button onClick={handleGenerate} disabled={loading}>
            {loading ? "Generiranje..." : "Generiraj predračun"}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}

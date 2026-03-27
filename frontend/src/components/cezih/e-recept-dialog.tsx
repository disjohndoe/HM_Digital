"use client"

import { useState } from "react"
import { Loader2, Plus, Trash2, Search } from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import { MockBadge } from "@/components/cezih/mock-badge"
import { useDrugSearch, useSendERecept } from "@/lib/hooks/use-cezih"
import type { LijekItem } from "@/lib/types"

interface SelectedDrug {
  atk: string
  naziv: string
  oblik: string
  kolicina: number
  doziranje: string
  napomena: string
}

interface EReceptDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  patientId: string
}

export function EReceptDialog({ open, onOpenChange, patientId }: EReceptDialogProps) {
  const [searchOpen, setSearchOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState("")
  const [selected, setSelected] = useState<SelectedDrug[]>([])
  const { data: drugs } = useDrugSearch(searchQuery)
  const sendERecept = useSendERecept()

  const handleAddDrug = (drug: LijekItem) => {
    if (selected.some((s) => s.atk === drug.atk && s.naziv === drug.naziv)) {
      toast.info("Lijek je već dodan")
      return
    }
    setSelected((prev) => [
      ...prev,
      {
        atk: drug.atk,
        naziv: drug.naziv,
        oblik: drug.oblik,
        kolicina: 1,
        doziranje: "",
        napomena: "",
      },
    ])
    setSearchOpen(false)
    setSearchQuery("")
  }

  const handleRemoveDrug = (index: number) => {
    setSelected((prev) => prev.filter((_, i) => i !== index))
  }

  const handleUpdateDrug = (index: number, field: keyof SelectedDrug, value: string | number) => {
    setSelected((prev) =>
      prev.map((drug, i) => (i === index ? { ...drug, [field]: value } : drug))
    )
  }

  const handleSubmit = () => {
    if (selected.length === 0) {
      toast.error("Dodajte barem jedan lijek")
      return
    }
    sendERecept.mutate(
      {
        patient_id: patientId,
        lijekovi: selected.map((d) => ({
          atk: d.atk,
          naziv: d.naziv,
          kolicina: d.kolicina,
          doziranje: d.doziranje,
          napomena: d.napomena,
        })),
      },
      {
        onSuccess: (data) => {
          toast.success(`e-Recept poslan (${data.recept_id})`)
          setSelected([])
          onOpenChange(false)
        },
        onError: (err) => toast.error(err.message),
      },
    )
  }

  const handleOpenChange = (open: boolean) => {
    if (!open) {
      setSelected([])
      setSearchQuery("")
    }
    onOpenChange(open)
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-2xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center gap-2">
            <DialogTitle>Pošalji e-Recept</DialogTitle>
            <MockBadge />
          </div>
        </DialogHeader>

        {/* Drug search */}
        <div className="space-y-4">
          <Popover open={searchOpen} onOpenChange={setSearchOpen}>
            <PopoverTrigger
              render={<Button variant="outline" className="w-full justify-start text-muted-foreground" />}
            >
              <Search className="mr-2 h-4 w-4" />
              Pretraži lijekove...
            </PopoverTrigger>
            <PopoverContent className="w-[--radix-popover-trigger-width] p-0" align="start">
              <Command shouldFilter={false}>
                <CommandInput
                  placeholder="Naziv ili ATK šifra..."
                  value={searchQuery}
                  onValueChange={setSearchQuery}
                />
                <CommandList>
                  <CommandEmpty>
                    {searchQuery.length < 2 ? "Unesite barem 2 znaka" : "Nema rezultata"}
                  </CommandEmpty>
                  {drugs && drugs.length > 0 && (
                    <CommandGroup>
                      {drugs.map((drug) => (
                        <CommandItem
                          key={`${drug.atk}-${drug.naziv}`}
                          value={drug.naziv}
                          onSelect={() => handleAddDrug(drug)}
                        >
                          <Plus className="mr-2 h-3 w-3" />
                          <div className="flex-1">
                            <p className="text-sm">{drug.naziv}</p>
                            <p className="text-xs text-muted-foreground">
                              {drug.oblik} · {drug.jacina} · ATK: {drug.atk}
                            </p>
                          </div>
                        </CommandItem>
                      ))}
                    </CommandGroup>
                  )}
                </CommandList>
              </Command>
            </PopoverContent>
          </Popover>

          {/* Selected drugs table */}
          {selected.length > 0 && (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Naziv</TableHead>
                  <TableHead className="hidden sm:table-cell">Oblik</TableHead>
                  <TableHead className="w-20">Kol.</TableHead>
                  <TableHead className="w-32">Doziranje</TableHead>
                  <TableHead className="hidden md:table-cell w-32">Napomena</TableHead>
                  <TableHead className="w-10"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {selected.map((drug, index) => (
                  <TableRow key={index}>
                    <TableCell className="text-sm font-medium">{drug.naziv}</TableCell>
                    <TableCell className="hidden sm:table-cell text-xs text-muted-foreground">
                      {drug.oblik}
                    </TableCell>
                    <TableCell>
                      <Input
                        type="number"
                        min={1}
                        value={drug.kolicina}
                        onChange={(e) => handleUpdateDrug(index, "kolicina", parseInt(e.target.value) || 1)}
                        className="h-8 w-16"
                      />
                    </TableCell>
                    <TableCell>
                      <Input
                        placeholder="npr. 1-0-1"
                        value={drug.doziranje}
                        onChange={(e) => handleUpdateDrug(index, "doziranje", e.target.value)}
                        className="h-8"
                      />
                    </TableCell>
                    <TableCell className="hidden md:table-cell">
                      <Input
                        placeholder="Napomena"
                        value={drug.napomena}
                        onChange={(e) => handleUpdateDrug(index, "napomena", e.target.value)}
                        className="h-8"
                      />
                    </TableCell>
                    <TableCell>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleRemoveDrug(index)}
                        className="h-8 w-8 p-0"
                      >
                        <Trash2 className="h-3 w-3 text-destructive" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => handleOpenChange(false)}>
            Odustani
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={sendERecept.isPending || selected.length === 0}
          >
            {sendERecept.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Pošalji e-Recept
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

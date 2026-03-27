"use client"

import { useForm } from "react-hook-form"
import { standardSchemaResolver } from "@hookform/resolvers/standard-schema"
import { z } from "zod"
import { Save, Loader2 } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { USER_ROLE_OPTIONS } from "@/lib/constants"
import type { User } from "@/lib/types"

const userSchema = z.object({
  email: z.string().email("Neispravan email"),
  password: z.string().min(6, "Lozinka mora imati najmanje 6 znakova").optional().or(z.literal("")),
  ime: z.string().min(1, "Ime je obavezno"),
  prezime: z.string().min(1, "Prezime je obavezno"),
  titula: z.string().nullable().optional(),
  telefon: z.string().nullable().optional(),
  role: z.string().min(1, "Uloga je obavezna"),
})

export type UserFormData = z.infer<typeof userSchema>

interface UserFormDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  user?: User | null
  onSubmit: (data: UserFormData) => void
  isPending: boolean
}

export function UserFormDialog({
  open,
  onOpenChange,
  user,
  onSubmit,
  isPending,
}: UserFormDialogProps) {
  const isEdit = !!user

  const {
    register,
    handleSubmit,
    setValue,
    reset,
    formState: { errors },
  } = useForm<UserFormData>({
    resolver: standardSchemaResolver(userSchema),
    defaultValues: {
      email: user?.email ?? "",
      password: "",
      ime: user?.ime ?? "",
      prezime: user?.prezime ?? "",
      titula: user?.titula ?? null,
      telefon: user?.telefon ?? null,
      role: user?.role ?? "doktor",
    },
  })

  const handleFormSubmit = (data: UserFormData) => {
    const payload = { ...data }
    if (isEdit && !payload.password) {
      delete payload.password
    }
    onSubmit(payload)
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(o) => {
        if (!o) reset()
        onOpenChange(o)
      }}
    >
      <DialogContent className="sm:max-w-[480px]">
        <DialogHeader>
          <DialogTitle>
            {isEdit ? "Uredi korisnika" : "Novi korisnik"}
          </DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="ime">Ime</Label>
              <Input id="ime" {...register("ime")} />
              {errors.ime && (
                <p className="text-xs text-destructive">{errors.ime.message}</p>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="prezime">Prezime</Label>
              <Input id="prezime" {...register("prezime")} />
              {errors.prezime && (
                <p className="text-xs text-destructive">
                  {errors.prezime.message}
                </p>
              )}
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="titula">Titula</Label>
            <Input id="titula" placeholder="dr. med., spec. ..." {...register("titula")} />
          </div>

          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input id="email" type="email" {...register("email")} />
            {errors.email && (
              <p className="text-xs text-destructive">{errors.email.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="password">
              {isEdit ? "Nova lozinka (prazno = nema promjene)" : "Lozinka"}
            </Label>
            <Input
              id="password"
              type="password"
              {...register("password")}
            />
            {errors.password && (
              <p className="text-xs text-destructive">
                {errors.password.message}
              </p>
            )}
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="telefon">Telefon</Label>
              <Input id="telefon" {...register("telefon")} />
            </div>
            <div className="space-y-2">
              <Label>Uloga</Label>
              <Select
                defaultValue={user?.role ?? "doktor"}
                onValueChange={(v) => setValue("role", v ?? "doktor")}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {USER_ROLE_OPTIONS.map((opt) => (
                    <SelectItem key={opt.value} value={opt.value}>
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {errors.role && (
                <p className="text-xs text-destructive">{errors.role.message}</p>
              )}
            </div>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              Odustani
            </Button>
            <Button type="submit" disabled={isPending}>
              {isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              <Save className="mr-2 h-4 w-4" />
              {isEdit ? "Spremi" : "Kreiraj"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

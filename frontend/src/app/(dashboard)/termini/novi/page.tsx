"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { ArrowLeftIcon } from "lucide-react"

import { Button } from "@/components/ui/button"
import { PageHeader } from "@/components/shared/page-header"
import { AppointmentForm } from "@/components/appointments/appointment-form"

export default function NoviTerminPage() {
  const router = useRouter()
  const [formOpen, setFormOpen] = useState(true)

  return (
    <div className="space-y-6">
      <PageHeader title="Novi termin" description="Zakazite novi termin za pacijenta">
        <Button variant="outline" nativeButton={false} render={<Link href="/termini" />}>
          <ArrowLeftIcon className="mr-2 h-4 w-4" />
          Natrag na kalendar
        </Button>
      </PageHeader>

      <AppointmentForm
        open={formOpen}
        onOpenChange={(open) => {
          setFormOpen(open)
          if (!open) router.push("/termini")
        }}
      />
    </div>
  )
}

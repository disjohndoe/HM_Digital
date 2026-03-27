"use client"

import { PageHeader } from "@/components/shared/page-header"
import { PatientForm } from "@/components/patients/patient-form"
import { useCreatePatient } from "@/lib/hooks/use-patients"

export default function NoviPacijentPage() {
  const createPatient = useCreatePatient()

  async function handleSubmit(data: Parameters<typeof createPatient.mutateAsync>[0]) {
    await createPatient.mutateAsync(data)
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Novi pacijent"
        description="Unesite podatke o novom pacijentu"
      />
      <PatientForm onSubmit={handleSubmit} isSubmitting={createPatient.isPending} />
    </div>
  )
}

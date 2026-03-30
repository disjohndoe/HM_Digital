"use client"

import { Download, Loader2 } from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { PageHeader } from "@/components/shared/page-header"
import { formatDateHR } from "@/lib/utils"
import { CezihStatusCard } from "@/components/cezih/cezih-status"
import { InsuranceCheck } from "@/components/cezih/insurance-check"
import { MockBadge } from "@/components/cezih/mock-badge"
import { CezihActivityLog } from "@/components/cezih/activity-log"
import { VisitManagement } from "@/components/cezih/visit-management"
import { CaseManagement } from "@/components/cezih/case-management"
import { ForeignerRegistration } from "@/components/cezih/foreigner-registration"
import { useRetrieveEUputnice, useEUputnice } from "@/lib/hooks/use-cezih"

export default function CezihPage() {
  const retrieveEUputnice = useRetrieveEUputnice()
  const { data: storedEUputnice } = useEUputnice()

  const handleRetrieveEUputnice = () => {
    retrieveEUputnice.mutate(undefined, {
      onSuccess: () => toast.success("e-Uputnice dohvaćene"),
      onError: (err) => toast.error(err.message),
    })
  }

  const euputnice = storedEUputnice?.items ?? []

  // Demo patient for visit/case management (in production, selected from patient list)
  const demoPatientId = ""
  const demoPatientMbo = ""

  return (
    <div className="space-y-6">
      <PageHeader title="CEZIH" />

      <div className="grid gap-6 lg:grid-cols-2">
        <CezihStatusCard />
        <InsuranceCheck />
      </div>

      <Tabs defaultValue="uputnice" className="space-y-4">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="uputnice">e-Uputnice</TabsTrigger>
          <TabsTrigger value="posjete">Posjete</TabsTrigger>
          <TabsTrigger value="slucajevi">Slučajevi</TabsTrigger>
          <TabsTrigger value="stranci">Stranci</TabsTrigger>
          <TabsTrigger value="aktivnost">Aktivnost</TabsTrigger>
        </TabsList>

        <TabsContent value="uputnice">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div className="flex items-center gap-2">
                <CardTitle className="text-lg">e-Uputnice</CardTitle>
                <MockBadge />
              </div>
              <Button
                onClick={handleRetrieveEUputnice}
                disabled={retrieveEUputnice.isPending}
              >
                {retrieveEUputnice.isPending ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Download className="mr-2 h-4 w-4" />
                )}
                Dohvati e-Uputnice
              </Button>
            </CardHeader>
            <CardContent>
              {euputnice.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-8">
                  <p className="text-sm text-muted-foreground">
                    Kliknite &quot;Dohvati e-Uputnice&quot; za prikaz primljenih uputnica
                  </p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="hidden sm:table-cell">ID</TableHead>
                      <TableHead>Datum</TableHead>
                      <TableHead>Svrha</TableHead>
                      <TableHead className="hidden md:table-cell">Izdavatelj</TableHead>
                      <TableHead className="hidden lg:table-cell">Specijalist</TableHead>
                      <TableHead>Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {euputnice.map((item) => (
                      <TableRow key={item.id}>
                        <TableCell className="hidden sm:table-cell font-mono text-xs">{item.id}</TableCell>
                        <TableCell>{formatDateHR(item.datum_izdavanja)}</TableCell>
                        <TableCell>{item.svrha}</TableCell>
                        <TableCell className="hidden md:table-cell max-w-[200px] truncate">{item.izdavatelj}</TableCell>
                        <TableCell className="hidden lg:table-cell max-w-[200px] truncate">{item.specijalist}</TableCell>
                        <TableCell>
                          <Badge
                            variant="outline"
                            className={
                              item.status === "Zatvorena"
                                ? "bg-green-100 text-green-800 border-green-200"
                                : "bg-orange-100 text-orange-800 border-orange-200"
                            }
                          >
                            {item.status}
                          </Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="posjete">
          <VisitManagement patientId={demoPatientId} patientMbo={demoPatientMbo} />
        </TabsContent>

        <TabsContent value="slucajevi">
          <CaseManagement patientId={demoPatientId} patientMbo={demoPatientMbo} />
        </TabsContent>

        <TabsContent value="stranci">
          <ForeignerRegistration />
        </TabsContent>

        <TabsContent value="aktivnost">
          <CezihActivityLog />
        </TabsContent>
      </Tabs>
    </div>
  )
}

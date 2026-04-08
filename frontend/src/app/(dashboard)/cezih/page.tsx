"use client"

import { useState, useEffect } from "react"
import { useSearchParams } from "next/navigation"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { PageHeader } from "@/components/shared/page-header"
import { CezihStatusCard } from "@/components/cezih/cezih-status"
import { InsuranceCheck } from "@/components/cezih/insurance-check"
import { CezihActivityLog } from "@/components/cezih/activity-log"
import { ForeignerRegistration } from "@/components/cezih/foreigner-registration"
import { RegistryTools } from "@/components/cezih/registry-tools"
import { toast } from "sonner"
import { usePermissions } from "@/lib/hooks/use-permissions"
import { useSettingsCezihStatus, useGenerateAgentSecret, useCreatePairingToken } from "@/lib/hooks/use-settings"

const VALID_TABS = ["stranci", "registri", "aktivnost", "postavke"]

export default function CezihPage() {
  const searchParams = useSearchParams()
  const tabParam = searchParams.get("tab")
  const defaultTab = tabParam && VALID_TABS.includes(tabParam) ? tabParam : "aktivnost"
  const { canViewCezih } = usePermissions()
  const { data: settingsStatus } = useSettingsCezihStatus()
  const generateSecret = useGenerateAgentSecret()
  const createPairingToken = useCreatePairingToken()
  const [generatedSecret, setGeneratedSecret] = useState<string | null>(null)
  const [generatedTenantId, setGeneratedTenantId] = useState<string | null>(null)
  const [copied, setCopied] = useState<string | null>(null)
  const [pairingFallback, setPairingFallback] = useState(false)

  useEffect(() => {
    if (settingsStatus?.agent_connected) {
      setGeneratedSecret(null)
      setGeneratedTenantId(null)
      setPairingFallback(false)
    }
  }, [settingsStatus?.agent_connected])

  const handleGenerate = async () => {
    try {
      const res = await generateSecret.mutateAsync()
      setGeneratedSecret(res.agent_secret)
      setGeneratedTenantId(res.tenant_id)
    } catch {
      // mutation error handled by react-query
    }
  }

  const handleCopy = async (text: string, key: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(key)
      setTimeout(() => setCopied(null), 2000)
    } catch {
      toast.error("Kopiranje nije uspjelo. Pokušajte ručno označiti tekst.")
    }
  }

  const handlePairAgent = async () => {
    setPairingFallback(false)
    try {
      if (!generatedSecret) {
        const res = await generateSecret.mutateAsync()
        setGeneratedSecret(res.agent_secret)
        setGeneratedTenantId(res.tenant_id)
      }
      const pairRes = await createPairingToken.mutateAsync()
      window.location.href = pairRes.pairing_url
      setTimeout(() => setPairingFallback(true), 3000)
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Greška pri povezivanju agenta")
    }
  }

  if (!canViewCezih) {
    return (
      <div className="space-y-6">
        <PageHeader title="CEZIH" />
        <div className="rounded-lg border border-destructive/50 bg-destructive/5 p-4">
          <p className="text-sm text-destructive">Nemate pristup ovoj stranici.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <PageHeader title="CEZIH" />

      <div className="grid gap-6 lg:grid-cols-2">
        <CezihStatusCard />
        <InsuranceCheck />
      </div>

      <Tabs defaultValue={defaultTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="stranci">Stranci</TabsTrigger>
          <TabsTrigger value="registri">Registri</TabsTrigger>
          <TabsTrigger value="aktivnost">Aktivnost</TabsTrigger>
          <TabsTrigger value="postavke">Postavke</TabsTrigger>
        </TabsList>

        <TabsContent value="stranci">
          <ForeignerRegistration />
        </TabsContent>

        <TabsContent value="registri">
          <RegistryTools />
        </TabsContent>

        <TabsContent value="aktivnost">
          <CezihActivityLog />
        </TabsContent>

        <TabsContent value="postavke">
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Konfiguracija</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4 sm:grid-cols-2">
                  <div>
                    <p className="text-sm text-muted-foreground">Šifra ustanove</p>
                    <p className="text-sm font-medium">
                      {settingsStatus?.sifra_ustanove || "Nije postavljena"}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">OID</p>
                    <p className="text-sm font-mono">
                      {settingsStatus?.oid || "Nije postavljen"}
                    </p>
                  </div>
                </div>

              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Lokalni agent</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center gap-2">
                  <span
                    className={`inline-block h-2.5 w-2.5 rounded-full ${
                      settingsStatus?.agent_connected
                        ? "bg-green-500"
                        : "bg-muted-foreground/50"
                    }`}
                  />
                  <span className="text-sm">
                    {settingsStatus?.agent_connected
                      ? "Agent je povezan"
                      : "Agent nije povezan"}
                  </span>
                </div>
                {settingsStatus?.last_heartbeat && (
                  <p className="text-xs text-muted-foreground">
                    Zadnji heartbeat: {new Date(settingsStatus.last_heartbeat).toLocaleString("hr-HR")}
                  </p>
                )}

                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={handleGenerate}
                      disabled={generateSecret.isPending || settingsStatus?.agent_connected}
                    >
                      {generateSecret.isPending
                        ? "Generiranje..."
                        : settingsStatus?.agent_connected
                          ? "Agent je već povezan"
                          : "Generiraj pristupne podatke"}
                    </Button>
                    {generatedSecret && !settingsStatus?.agent_connected && (
                      <Button
                        size="sm"
                        onClick={handlePairAgent}
                        disabled={createPairingToken.isPending}
                      >
                        {createPairingToken.isPending ? "Povezivanje..." : "Poveži agenta"}
                      </Button>
                    )}
                  </div>

                  {pairingFallback && (
                    <p className="text-xs text-amber-600">
                      Agent se nije pokrenuo? Provjerite je li <strong>HM Digital Agent</strong> instaliran na ovom računalu.
                    </p>
                  )}

                  {generatedSecret && generatedTenantId && (
                    <div className="rounded-md bg-muted p-3 space-y-2">
                      <div>
                        <div className="flex items-center justify-between mb-1">
                          <p className="text-xs font-medium text-muted-foreground">Tenant ID</p>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-5 text-xs px-1"
                            onClick={() => handleCopy(generatedTenantId, "tenant")}
                          >
                            {copied === "tenant" ? "Kopirano!" : "Kopiraj"}
                          </Button>
                        </div>
                        <code className="block break-all text-xs">{generatedTenantId}</code>
                      </div>
                      <div>
                        <div className="flex items-center justify-between mb-1">
                          <p className="text-xs font-medium text-muted-foreground">Tajni ključ</p>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-5 text-xs px-1"
                            onClick={() => handleCopy(generatedSecret, "secret")}
                          >
                            {copied === "secret" ? "Kopirano!" : "Kopiraj"}
                          </Button>
                        </div>
                        <code className="block break-all text-xs">{generatedSecret}</code>
                      </div>
                    </div>
                  )}

                  <div className="rounded-md border p-3">
                    <p className="mb-2 text-sm font-medium">Upute za postavljanje</p>
                    <ol className="list-inside list-decimal space-y-1 text-sm text-muted-foreground">
                      <li>Kliknite <strong>"Generiraj pristupne podatke"</strong> — dobit ćete Tenant ID i tajni ključ</li>
                      <li>Instalirajte <strong>HM Digital Agent</strong> na računalo u ordinaciji</li>
                      <li>Kliknite <strong>"Poveži agenta"</strong> — agent će se automatski konfigurirati</li>
                    </ol>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { useCezihConnectionDisplay } from "@/lib/hooks/use-cezih"

function StatusRow({ dotClass, label, detail }: {
  dotClass: string
  label: string
  detail?: string | null
}) {
  return (
    <div className="flex items-center gap-2">
      <span className={`inline-block h-2.5 w-2.5 rounded-full shrink-0 ${dotClass}`} />
      <span className="text-sm">{label}</span>
      {detail && (
        <span className="text-xs text-muted-foreground ml-auto truncate max-w-[140px]">
          {detail}
        </span>
      )}
    </div>
  )
}

export function CezihStatusCard() {
  const cezih = useCezihConnectionDisplay()

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-lg">Status veze</CardTitle>
      </CardHeader>
      <CardContent>
        {cezih.isLoading ? (
          <div className="text-sm text-muted-foreground">Učitavanje...</div>
        ) : cezih.isError ? (
          <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-3">
            <p className="text-sm text-destructive">
              Greška pri dohvatu CEZIH statusa: {(cezih.error as Error)?.message ?? "Nepoznata greška"}
            </p>
          </div>
        ) : cezih.raw ? (
          <div className="space-y-2.5">
            <StatusRow dotClass={cezih.agent.dotClass} label={cezih.agent.label} />
            <StatusRow dotClass={cezih.card.dotClass} label={cezih.card.label} detail={cezih.card.detail} />
            <StatusRow dotClass={cezih.vpn.dotClass} label={cezih.vpn.label} />
            {cezih.connectedDoctor && (
              <div className="pt-1.5 border-t text-sm text-muted-foreground">
                {cezih.connectedDoctor}
                {cezih.connectedClinic && <> &mdash; {cezih.connectedClinic}</>}
              </div>
            )}
          </div>
        ) : null}
      </CardContent>
    </Card>
  )
}

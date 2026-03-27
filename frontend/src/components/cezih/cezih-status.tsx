import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { useCezihStatus } from "@/lib/hooks/use-cezih"
import { MockBadge } from "./mock-badge"

export function CezihStatusCard() {
  const { data, isLoading } = useCezihStatus()

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-lg">Status veze</CardTitle>
        {data?.mock && <MockBadge />}
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="text-sm text-muted-foreground">Učitavanje...</div>
        ) : data ? (
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <span
                className={`inline-block h-2.5 w-2.5 rounded-full ${
                  data.connected ? "bg-green-500" : "bg-muted-foreground/50"
                }`}
              />
              <span className="text-sm">
                {data.connected ? "Povezano" : "Nije povezano"}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">Način:</span>
              <Badge variant="outline">{data.mode}</Badge>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">Agent:</span>
              <span className="text-sm">
                {data.agent_connected ? "Povezan" : "Nije povezan"}
              </span>
            </div>
          </div>
        ) : null}
      </CardContent>
    </Card>
  )
}

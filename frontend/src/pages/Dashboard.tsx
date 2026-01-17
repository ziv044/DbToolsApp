import { Card, CardHeader, CardContent } from '../components/ui'
import { useTenantStore } from '../stores/tenantStore'

export const Dashboard = () => {
  const { tenantData, currentTenant } = useTenantStore()

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">
        Welcome to {tenantData?.name || currentTenant || 'DbTools'}
      </h1>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold">Servers</h2>
          </CardHeader>
          <CardContent>
            <p className="text-gray-600">No servers configured yet.</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold">Active Jobs</h2>
          </CardHeader>
          <CardContent>
            <p className="text-gray-600">No active jobs.</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold">Recent Alerts</h2>
          </CardHeader>
          <CardContent>
            <p className="text-gray-600">No recent alerts.</p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

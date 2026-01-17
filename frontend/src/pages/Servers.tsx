import { Card, CardHeader, CardContent } from '../components/ui'

export const Servers = () => {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Servers</h1>
      <Card>
        <CardHeader>
          <h2 className="text-lg font-semibold">SQL Server Connections</h2>
        </CardHeader>
        <CardContent>
          <p className="text-gray-600">Server management will be implemented in Epic 2.</p>
        </CardContent>
      </Card>
    </div>
  )
}

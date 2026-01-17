import { Card, CardHeader, CardContent } from '../components/ui'

export const Policies = () => {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Policies</h1>
      <Card>
        <CardHeader>
          <h2 className="text-lg font-semibold">Monitoring Policies</h2>
        </CardHeader>
        <CardContent>
          <p className="text-gray-600">Policy management will be implemented in Epic 4.</p>
        </CardContent>
      </Card>
    </div>
  )
}

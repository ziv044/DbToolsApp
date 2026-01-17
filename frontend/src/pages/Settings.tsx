import { Card, CardHeader, CardContent } from '../components/ui'

export const Settings = () => {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
      <Card>
        <CardHeader>
          <h2 className="text-lg font-semibold">Application Settings</h2>
        </CardHeader>
        <CardContent>
          <p className="text-gray-600">Settings configuration coming soon.</p>
        </CardContent>
      </Card>
    </div>
  )
}

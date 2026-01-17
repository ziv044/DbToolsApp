import { Card, CardHeader, CardContent } from '../components/ui'

export const Groups = () => {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Server Groups</h1>
      <Card>
        <CardHeader>
          <h2 className="text-lg font-semibold">Manage Groups</h2>
        </CardHeader>
        <CardContent>
          <p className="text-gray-600">Server group management will be implemented in Epic 2.</p>
        </CardContent>
      </Card>
    </div>
  )
}

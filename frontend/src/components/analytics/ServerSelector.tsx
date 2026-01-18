import { useQuery } from '@tanstack/react-query'
import { Server } from 'lucide-react'
import { apiClient } from '../../services/api'

interface ServerSelectorProps {
  value: string | null
  onChange: (serverId: string) => void
}

interface ServerItem {
  id: string
  name: string
  status: string
}

export const ServerSelector = ({ value, onChange }: ServerSelectorProps) => {
  const { data, isLoading } = useQuery({
    queryKey: ['servers-list'],
    queryFn: async () => {
      const response = await apiClient.get('/servers')
      return response.data.servers as ServerItem[]
    }
  })

  // Filter to only servers that might have collection enabled
  const servers = data?.filter(s => s.status !== 'unknown') || []

  return (
    <div className="relative">
      <div className="flex items-center">
        <Server className="absolute left-3 h-4 w-4 text-gray-400" />
        <select
          value={value || ''}
          onChange={(e) => onChange(e.target.value)}
          className="pl-9 pr-8 py-2 text-sm border border-gray-300 rounded-lg bg-white
            focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
            appearance-none cursor-pointer min-w-48"
        >
          <option value="">
            {isLoading ? 'Loading...' : 'Select a server'}
          </option>
          {servers.map(server => (
            <option key={server.id} value={server.id}>
              {server.name}
            </option>
          ))}
        </select>
        <div className="absolute right-3 pointer-events-none">
          <svg className="h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </div>
    </div>
  )
}

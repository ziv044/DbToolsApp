import { Copy } from 'lucide-react'
import { Modal, Button, Badge } from '../ui'

interface QueryDetailModalProps {
  query: Record<string, unknown> | null
  onClose: () => void
}

export const QueryDetailModal = ({ query, onClose }: QueryDetailModalProps) => {
  if (!query) return null

  const copyToClipboard = () => {
    const text = query.query_text as string
    if (text) {
      navigator.clipboard.writeText(text)
    }
  }

  const durationSec = query.duration_ms ? ((query.duration_ms as number) / 1000).toFixed(2) : 'N/A'

  return (
    <Modal isOpen={!!query} onClose={onClose} title={`Session ${query.session_id}`} size="lg">
      <div className="space-y-4">
        {/* Status badges */}
        <div className="flex items-center gap-2">
          <Badge variant={query.status === 'running' ? 'info' : 'default'}>
            {String(query.status ?? '')}
          </Badge>
          {!!query.blocking_session_id && (
            <Badge variant="error">
              Blocked by {String(query.blocking_session_id)}
            </Badge>
          )}
          {!!query.wait_type && (
            <Badge variant="warning">
              Waiting: {String(query.wait_type)}
            </Badge>
          )}
        </div>

        {/* Metadata Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <div className="text-gray-500 text-xs uppercase">Database</div>
            <div className="font-medium">{String(query.database_name ?? 'N/A')}</div>
          </div>
          <div>
            <div className="text-gray-500 text-xs uppercase">Login</div>
            <div className="font-medium">{(query.login_name as string) || 'N/A'}</div>
          </div>
          <div>
            <div className="text-gray-500 text-xs uppercase">Host</div>
            <div className="font-medium">{(query.host_name as string) || 'N/A'}</div>
          </div>
          <div>
            <div className="text-gray-500 text-xs uppercase">Application</div>
            <div className="font-medium truncate" title={query.program_name as string}>
              {(query.program_name as string) || 'N/A'}
            </div>
          </div>
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-sm bg-gray-50 p-4 rounded-lg">
          <div>
            <div className="text-gray-500 text-xs uppercase">Duration</div>
            <div className="font-mono font-bold text-lg text-blue-600">{durationSec}s</div>
          </div>
          <div>
            <div className="text-gray-500 text-xs uppercase">CPU Time</div>
            <div className="font-mono">{((query.cpu_time_ms as number) || 0).toLocaleString()} ms</div>
          </div>
          <div>
            <div className="text-gray-500 text-xs uppercase">Logical Reads</div>
            <div className="font-mono">{((query.logical_reads as number) || 0).toLocaleString()}</div>
          </div>
          <div>
            <div className="text-gray-500 text-xs uppercase">Physical Reads</div>
            <div className="font-mono">{((query.physical_reads as number) || 0).toLocaleString()}</div>
          </div>
          <div>
            <div className="text-gray-500 text-xs uppercase">Writes</div>
            <div className="font-mono">{((query.writes as number) || 0).toLocaleString()}</div>
          </div>
        </div>

        {/* Wait Info */}
        {!!query.wait_type && (
          <div className="bg-yellow-50 p-3 rounded-lg border border-yellow-200">
            <span className="text-yellow-800 font-medium">Waiting on: </span>
            <span className="font-mono">{String(query.wait_type)}</span>
            {!!query.wait_time_ms && (
              <span className="text-gray-500 ml-2">
                ({(Number(query.wait_time_ms) || 0).toLocaleString()} ms)
              </span>
            )}
          </div>
        )}

        {/* Query Text */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <div className="text-gray-500 text-xs uppercase">Query Text</div>
            <Button variant="ghost" size="sm" onClick={copyToClipboard}>
              <Copy size={14} className="mr-1" /> Copy
            </Button>
          </div>
          <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg text-xs overflow-auto max-h-64 font-mono whitespace-pre-wrap">
            {(query.query_text as string) || 'No query text available'}
          </pre>
        </div>

        {/* Close Button */}
        <div className="flex justify-end pt-2">
          <Button variant="secondary" onClick={onClose}>
            Close
          </Button>
        </div>
      </div>
    </Modal>
  )
}

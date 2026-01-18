import { useState } from 'react'
import { AlertTriangle, ChevronRight, ChevronDown } from 'lucide-react'
import { Panel } from './Panel'

interface BlockingNode {
  session_id: number
  login_name: string | null
  host_name: string | null
  program_name: string | null
  database_name: string | null
  query_text: string | null
  duration_ms: number | null
  cpu_time_ms: number | null
  wait_type: string | null
  blocked: BlockingNode[]
}

interface BlockingTreePanelProps {
  title: string
  chains: BlockingNode[] | null | undefined
  totalBlocked?: number
  isLoading: boolean
  error?: Error | null
  onQueryClick?: (node: BlockingNode) => void
  height?: number
}

interface TreeNodeProps {
  node: BlockingNode
  depth: number
  onQueryClick?: (node: BlockingNode) => void
}

const TreeNode = ({ node, depth, onQueryClick }: TreeNodeProps) => {
  const [expanded, setExpanded] = useState(true)
  const hasChildren = node.blocked && node.blocked.length > 0
  const durationSec = node.duration_ms ? (node.duration_ms / 1000).toFixed(1) : '?'

  return (
    <div className="select-none">
      <div
        className={`flex items-center gap-2 py-1.5 px-2 rounded cursor-pointer transition-colors
          ${depth === 0
            ? 'bg-red-50 border-l-4 border-red-500 hover:bg-red-100'
            : 'ml-6 border-l-2 border-yellow-400 hover:bg-yellow-50'
          }`}
        onClick={() => onQueryClick?.(node)}
      >
        {hasChildren ? (
          <button
            onClick={(e) => { e.stopPropagation(); setExpanded(!expanded) }}
            className="p-0.5 hover:bg-gray-200 rounded"
          >
            {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
          </button>
        ) : (
          <span className="w-5" />
        )}

        {depth === 0 && <AlertTriangle size={14} className="text-red-500 flex-shrink-0" />}

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 text-xs">
            <span className="font-mono font-bold text-gray-900">SPID {node.session_id}</span>
            <span className="text-gray-500">{node.login_name || 'unknown'}</span>
            <span className="text-gray-300">|</span>
            <span className="text-gray-500">{node.database_name || 'unknown'}</span>
            <span className="text-gray-300">|</span>
            <span className={`font-medium ${(node.duration_ms || 0) > 30000 ? 'text-red-600' : 'text-gray-600'}`}>
              {durationSec}s
            </span>
          </div>
          <div className="text-xs text-gray-500 truncate mt-0.5">
            {node.query_text?.slice(0, 80) || 'No query text'}
          </div>
        </div>

        {node.wait_type && (
          <span className="text-xs bg-yellow-100 text-yellow-800 px-1.5 py-0.5 rounded flex-shrink-0">
            {node.wait_type}
          </span>
        )}
      </div>

      {expanded && hasChildren && (
        <div className="ml-4">
          {node.blocked.map((child, i) => (
            <TreeNode key={`${child.session_id}-${i}`} node={child} depth={depth + 1} onQueryClick={onQueryClick} />
          ))}
        </div>
      )}
    </div>
  )
}

const countBlocked = (node: BlockingNode): number => {
  if (!node || !node.blocked) return 0
  return node.blocked.length + node.blocked.reduce((sum, c) => sum + countBlocked(c), 0)
}

export const BlockingTreePanel = ({
  title,
  chains,
  totalBlocked,
  isLoading,
  error,
  onQueryClick,
  height = 350
}: BlockingTreePanelProps) => {
  const blockedCount = totalBlocked ?? chains?.reduce((sum, c) => sum + countBlocked(c), 0) ?? 0

  return (
    <Panel
      title={title}
      subtitle={blockedCount > 0 ? `${blockedCount} blocked session(s)` : undefined}
      isLoading={isLoading}
      error={error}
      isEmpty={!chains?.length}
      emptyMessage="No blocking chains detected"
      height={height}
    >
      <div className="space-y-2 overflow-auto h-full -mx-2">
        {chains?.map((chain, i) => (
          <TreeNode key={`${chain.session_id}-${i}`} node={chain} depth={0} onQueryClick={onQueryClick} />
        ))}
      </div>
    </Panel>
  )
}

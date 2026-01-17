import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import {
  Plus,
  Play,
  Pause,
  PlayCircle,
  Trash2,
  RefreshCw,
  Calendar,
  AlertCircle,
  CheckCircle,
  Clock,
  XCircle,
} from 'lucide-react'
import { Card, CardHeader, CardContent, Button, Spinner } from '../components/ui'
import {
  jobService,
  JOB_TYPE_LABELS,
  JOB_TYPE_ICONS,
  formatSchedule,
} from '../services/jobService'
import type { Job, JobType, ExecutionStatus } from '../services/jobService'
import { toast } from '../components/ui/toastStore'
import { CreateJobModal } from '../components/jobs'

const JOB_TYPES: JobType[] = ['policy_execution', 'data_collection', 'custom_script', 'alert_check']

export const Jobs = () => {
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
  const [typeFilter, setTypeFilter] = useState<JobType | ''>('')
  const [enabledFilter, setEnabledFilter] = useState<'all' | 'enabled' | 'disabled'>('all')
  const [isTabVisible, setIsTabVisible] = useState(!document.hidden)
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  // Handle visibility change - pause polling when tab is hidden
  useEffect(() => {
    const handleVisibilityChange = () => {
      const visible = !document.hidden
      setIsTabVisible(visible)
      if (visible) {
        queryClient.invalidateQueries({ queryKey: ['jobs'] })
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange)
  }, [queryClient])

  const { data, isLoading, refetch, isFetching } = useQuery({
    queryKey: ['jobs', typeFilter, enabledFilter],
    queryFn: () =>
      jobService.getAll({
        type: typeFilter || undefined,
        enabled: enabledFilter === 'all' ? undefined : enabledFilter === 'enabled',
      }),
    refetchInterval: isTabVisible ? 30_000 : false,
  })

  const runNowMutation = useMutation({
    mutationFn: (jobId: string) => jobService.runNow(jobId),
    onSuccess: () => {
      toast.success('Job queued for immediate execution')
      queryClient.invalidateQueries({ queryKey: ['jobs'] })
    },
    onError: () => toast.error('Failed to run job'),
  })

  const enableMutation = useMutation({
    mutationFn: (jobId: string) => jobService.enable(jobId),
    onSuccess: () => {
      toast.success('Job enabled')
      queryClient.invalidateQueries({ queryKey: ['jobs'] })
    },
    onError: () => toast.error('Failed to enable job'),
  })

  const disableMutation = useMutation({
    mutationFn: (jobId: string) => jobService.disable(jobId),
    onSuccess: () => {
      toast.success('Job disabled')
      queryClient.invalidateQueries({ queryKey: ['jobs'] })
    },
    onError: () => toast.error('Failed to disable job'),
  })

  const deleteMutation = useMutation({
    mutationFn: (jobId: string) => jobService.delete(jobId),
    onSuccess: () => {
      toast.success('Job deleted')
      queryClient.invalidateQueries({ queryKey: ['jobs'] })
    },
    onError: () => toast.error('Failed to delete job'),
  })

  const handleDelete = (job: Job) => {
    if (window.confirm(`Delete job "${job.name}"?`)) {
      deleteMutation.mutate(job.id)
    }
  }

  const jobs = data?.jobs ?? []

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Scheduled Jobs</h1>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={() => refetch()} disabled={isFetching}>
            <RefreshCw className={`h-4 w-4 mr-2 ${isFetching ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button onClick={() => setIsCreateModalOpen(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Create Job
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-4">
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value as JobType | '')}
          className="px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">All Types</option>
          {JOB_TYPES.map((type) => (
            <option key={type} value={type}>
              {JOB_TYPE_LABELS[type]}
            </option>
          ))}
        </select>

        <select
          value={enabledFilter}
          onChange={(e) => setEnabledFilter(e.target.value as 'all' | 'enabled' | 'disabled')}
          className="px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="all">All Status</option>
          <option value="enabled">Enabled</option>
          <option value="disabled">Disabled</option>
        </select>
      </div>

      <Card>
        <CardHeader>
          <h2 className="text-lg font-semibold">Jobs</h2>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Spinner size="lg" />
            </div>
          ) : jobs.length === 0 ? (
            <div className="text-center py-12">
              <Calendar className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No jobs</h3>
              <p className="mt-1 text-sm text-gray-500">
                Get started by creating a scheduled job.
              </p>
              <div className="mt-6">
                <Button onClick={() => setIsCreateModalOpen(true)}>
                  <Plus className="h-4 w-4 mr-2" />
                  Create Job
                </Button>
              </div>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b text-left text-sm text-gray-500">
                    <th className="pb-3 font-medium">Name</th>
                    <th className="pb-3 font-medium">Type</th>
                    <th className="pb-3 font-medium">Schedule</th>
                    <th className="pb-3 font-medium">Next Run</th>
                    <th className="pb-3 font-medium">Last Run</th>
                    <th className="pb-3 font-medium">Status</th>
                    <th className="pb-3 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {jobs.map((job) => (
                    <JobRow
                      key={job.id}
                      job={job}
                      onRowClick={() => navigate(`/jobs/${job.id}`)}
                      onRunNow={() => runNowMutation.mutate(job.id)}
                      onEnable={() => enableMutation.mutate(job.id)}
                      onDisable={() => disableMutation.mutate(job.id)}
                      onDelete={() => handleDelete(job)}
                    />
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      <CreateJobModal isOpen={isCreateModalOpen} onClose={() => setIsCreateModalOpen(false)} />
    </div>
  )
}

interface JobRowProps {
  job: Job
  onRowClick: () => void
  onRunNow: () => void
  onEnable: () => void
  onDisable: () => void
  onDelete: () => void
}

const JobRow = ({ job, onRowClick, onRunNow, onEnable, onDisable, onDelete }: JobRowProps) => {
  const isRunning = job.last_status === 'running'

  return (
    <tr
      className="border-b last:border-0 hover:bg-gray-50 cursor-pointer"
      onClick={onRowClick}
    >
      <td className="py-3">
        <div className="flex items-center gap-2">
          <span className="text-lg">{JOB_TYPE_ICONS[job.type]}</span>
          <span className="font-medium">{job.name}</span>
          {job.last_status === 'failed' && (
            <span title="Last execution failed">
              <AlertCircle className="h-4 w-4 text-red-500" />
            </span>
          )}
        </div>
      </td>
      <td className="py-3 text-sm text-gray-600">{JOB_TYPE_LABELS[job.type]}</td>
      <td className="py-3 text-sm text-gray-600">
        {formatSchedule(job.schedule_type, job.schedule_config)}
      </td>
      <td className="py-3 text-sm">
        {job.next_run_at ? (
          <span className="text-gray-600">
            {new Date(job.next_run_at).toLocaleString()}
          </span>
        ) : (
          <span className="text-gray-400">-</span>
        )}
      </td>
      <td className="py-3 text-sm">
        {job.last_execution_at ? (
          <span className="text-gray-600">
            {new Date(job.last_execution_at).toLocaleString()}
          </span>
        ) : (
          <span className="text-gray-400">Never</span>
        )}
      </td>
      <td className="py-3">
        <StatusBadge isEnabled={job.is_enabled} lastStatus={job.last_status} isRunning={isRunning} />
      </td>
      <td className="py-3">
        <div className="flex gap-1" onClick={(e) => e.stopPropagation()}>
          <button
            onClick={onRunNow}
            className="p-1.5 text-blue-600 hover:bg-blue-50 rounded"
            title="Run Now"
          >
            <PlayCircle className="h-4 w-4" />
          </button>
          {job.is_enabled ? (
            <button
              onClick={onDisable}
              className="p-1.5 text-gray-600 hover:bg-gray-100 rounded"
              title="Disable"
            >
              <Pause className="h-4 w-4" />
            </button>
          ) : (
            <button
              onClick={onEnable}
              className="p-1.5 text-green-600 hover:bg-green-50 rounded"
              title="Enable"
            >
              <Play className="h-4 w-4" />
            </button>
          )}
          <button
            onClick={onDelete}
            className="p-1.5 text-red-600 hover:bg-red-50 rounded"
            title="Delete"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </td>
    </tr>
  )
}

interface StatusBadgeProps {
  isEnabled: boolean
  lastStatus?: ExecutionStatus | null
  isRunning: boolean
}

const StatusBadge = ({ isEnabled, lastStatus, isRunning }: StatusBadgeProps) => {
  if (isRunning) {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs rounded-full bg-blue-100 text-blue-800">
        <Spinner size="sm" />
        Running
      </span>
    )
  }

  if (!isEnabled) {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs rounded-full bg-gray-100 text-gray-600">
        <Pause className="h-3 w-3" />
        Disabled
      </span>
    )
  }

  // Show last status with enabled state
  const statusConfig: Record<ExecutionStatus, { icon: typeof CheckCircle; color: string; label: string }> = {
    success: { icon: CheckCircle, color: 'bg-green-100 text-green-800', label: 'Success' },
    failed: { icon: XCircle, color: 'bg-red-100 text-red-800', label: 'Failed' },
    pending: { icon: Clock, color: 'bg-yellow-100 text-yellow-800', label: 'Pending' },
    running: { icon: Clock, color: 'bg-blue-100 text-blue-800', label: 'Running' },
    cancelled: { icon: XCircle, color: 'bg-gray-100 text-gray-600', label: 'Cancelled' },
  }

  if (lastStatus && statusConfig[lastStatus]) {
    const { icon: Icon, color, label } = statusConfig[lastStatus]
    return (
      <span className={`inline-flex items-center gap-1 px-2 py-0.5 text-xs rounded-full ${color}`}>
        <Icon className="h-3 w-3" />
        {label}
      </span>
    )
  }

  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs rounded-full bg-green-100 text-green-800">
      <CheckCircle className="h-3 w-3" />
      Enabled
    </span>
  )
}

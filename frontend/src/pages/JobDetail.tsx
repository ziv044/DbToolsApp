import { useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  ArrowLeft,
  Edit2,
  Trash2,
  PlayCircle,
  Settings,
  History,
  Play,
  Pause,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react'
import { Card, CardHeader, CardContent, Button, Spinner } from '../components/ui'
import {
  jobService,
  JOB_TYPE_LABELS,
  JOB_TYPE_ICONS,
  SCHEDULE_TYPE_LABELS,
  formatSchedule,
} from '../services/jobService'
import type { Job, JobExecution, ExecutionStatus } from '../services/jobService'
import { toast } from '../components/ui/toastStore'

const EXECUTIONS_PER_PAGE = 20

export const JobDetail = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState<'config' | 'executions'>('config')
  const [executionPage, setExecutionPage] = useState(0)
  const [selectedExecution, setSelectedExecution] = useState<JobExecution | null>(null)

  const { data: job, isLoading: jobLoading } = useQuery({
    queryKey: ['job', id],
    queryFn: () => jobService.get(id!),
    enabled: !!id,
  })

  const { data: executionsData, isLoading: executionsLoading } = useQuery({
    queryKey: ['job-executions', id, executionPage],
    queryFn: () =>
      jobService.getExecutions(id!, {
        limit: EXECUTIONS_PER_PAGE,
        offset: executionPage * EXECUTIONS_PER_PAGE,
      }),
    enabled: !!id && activeTab === 'executions',
  })

  const runNowMutation = useMutation({
    mutationFn: () => jobService.runNow(id!),
    onSuccess: () => {
      toast.success('Job queued for immediate execution')
      queryClient.invalidateQueries({ queryKey: ['job', id] })
      queryClient.invalidateQueries({ queryKey: ['job-executions', id] })
    },
    onError: () => toast.error('Failed to run job'),
  })

  const enableMutation = useMutation({
    mutationFn: () => jobService.enable(id!),
    onSuccess: () => {
      toast.success('Job enabled')
      queryClient.invalidateQueries({ queryKey: ['job', id] })
    },
    onError: () => toast.error('Failed to enable job'),
  })

  const disableMutation = useMutation({
    mutationFn: () => jobService.disable(id!),
    onSuccess: () => {
      toast.success('Job disabled')
      queryClient.invalidateQueries({ queryKey: ['job', id] })
    },
    onError: () => toast.error('Failed to disable job'),
  })

  const deleteMutation = useMutation({
    mutationFn: () => jobService.delete(id!),
    onSuccess: () => {
      toast.success('Job deleted')
      queryClient.invalidateQueries({ queryKey: ['jobs'] })
      navigate('/jobs')
    },
    onError: () => toast.error('Failed to delete job'),
  })

  const handleDelete = () => {
    if (window.confirm('Are you sure you want to delete this job?')) {
      deleteMutation.mutate()
    }
  }

  if (jobLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Spinner size="lg" />
      </div>
    )
  }

  if (!job) {
    return (
      <div className="text-center py-12">
        <h2 className="text-xl font-semibold text-gray-900">Job not found</h2>
        <Link to="/jobs" className="text-blue-600 hover:underline mt-2 inline-block">
          Back to Jobs
        </Link>
      </div>
    )
  }

  const executions = executionsData?.executions ?? []
  const totalExecutions = executionsData?.total ?? 0
  const totalPages = Math.ceil(totalExecutions / EXECUTIONS_PER_PAGE)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link to="/jobs" className="text-gray-400 hover:text-gray-600">
            <ArrowLeft className="h-6 w-6" />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-2xl">{JOB_TYPE_ICONS[job.type]}</span>
              <h1 className="text-2xl font-bold text-gray-900">{job.name}</h1>
              <JobStatusBadge job={job} />
            </div>
            <p className="text-gray-500 mt-1">{JOB_TYPE_LABELS[job.type]}</p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button
            variant="primary"
            onClick={() => runNowMutation.mutate()}
            disabled={runNowMutation.isPending}
          >
            <PlayCircle className="h-4 w-4 mr-2" />
            Run Now
          </Button>
          {job.is_enabled ? (
            <Button
              variant="secondary"
              onClick={() => disableMutation.mutate()}
              disabled={disableMutation.isPending}
            >
              <Pause className="h-4 w-4 mr-2" />
              Disable
            </Button>
          ) : (
            <Button
              variant="secondary"
              onClick={() => enableMutation.mutate()}
              disabled={enableMutation.isPending}
            >
              <Play className="h-4 w-4 mr-2" />
              Enable
            </Button>
          )}
          <Button variant="secondary" onClick={() => navigate(`/jobs/${id}/edit`)}>
            <Edit2 className="h-4 w-4 mr-2" />
            Edit
          </Button>
          <Button variant="danger" onClick={handleDelete} disabled={deleteMutation.isPending}>
            <Trash2 className="h-4 w-4 mr-2" />
            Delete
          </Button>
        </div>
      </div>

      {/* Schedule Summary */}
      <Card>
        <CardContent className="py-4">
          <div className="flex items-center gap-6">
            <div>
              <span className="text-sm text-gray-500">Schedule</span>
              <p className="font-medium">
                {formatSchedule(job.schedule_type, job.schedule_config)}
              </p>
            </div>
            <div>
              <span className="text-sm text-gray-500">Next Run</span>
              <p className="font-medium">
                {job.next_run_at ? new Date(job.next_run_at).toLocaleString() : 'Not scheduled'}
              </p>
            </div>
            <div>
              <span className="text-sm text-gray-500">Last Run</span>
              <p className="font-medium">
                {job.last_run_at ? new Date(job.last_run_at).toLocaleString() : 'Never'}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tabs */}
      <div className="border-b">
        <nav className="flex gap-6">
          {[
            { id: 'config', label: 'Configuration', icon: Settings },
            { id: 'executions', label: `Execution History (${totalExecutions})`, icon: History },
          ].map(({ id: tabId, label, icon: Icon }) => (
            <button
              key={tabId}
              onClick={() => setActiveTab(tabId as typeof activeTab)}
              className={`flex items-center gap-2 py-3 border-b-2 -mb-px transition-colors ${
                activeTab === tabId
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              <Icon className="h-4 w-4" />
              {label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'config' && <ConfigurationTab job={job} />}
      {activeTab === 'executions' && (
        <ExecutionsTab
          executions={executions}
          loading={executionsLoading}
          page={executionPage}
          totalPages={totalPages}
          onPageChange={setExecutionPage}
          selectedExecution={selectedExecution}
          onSelectExecution={setSelectedExecution}
        />
      )}
    </div>
  )
}

const JobStatusBadge = ({ job }: { job: Job }) => {
  if (job.last_status === 'running') {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs rounded-full bg-blue-100 text-blue-800">
        <Spinner size="sm" />
        Running
      </span>
    )
  }

  if (!job.is_enabled) {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs rounded-full bg-gray-100 text-gray-600">
        <Pause className="h-3 w-3" />
        Disabled
      </span>
    )
  }

  if (job.last_status === 'failed') {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs rounded-full bg-red-100 text-red-800">
        <AlertCircle className="h-3 w-3" />
        Last Failed
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

const ConfigurationTab = ({ job }: { job: Job }) => {
  const scheduleEntries = Object.entries(job.schedule_config)
  const configEntries = Object.entries(job.configuration)

  return (
    <div className="grid grid-cols-2 gap-6">
      <Card>
        <CardHeader>
          <h3 className="font-semibold">Schedule Configuration</h3>
        </CardHeader>
        <CardContent>
          <dl className="space-y-3">
            <div className="border-b pb-2">
              <dt className="text-sm text-gray-500">Schedule Type</dt>
              <dd className="font-medium">{SCHEDULE_TYPE_LABELS[job.schedule_type]}</dd>
            </div>
            {scheduleEntries.map(([key, value]) => (
              <div key={key} className="border-b pb-2">
                <dt className="text-sm text-gray-500">{formatLabel(key)}</dt>
                <dd className="font-medium">{formatValue(value)}</dd>
              </div>
            ))}
          </dl>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <h3 className="font-semibold">Job Configuration</h3>
        </CardHeader>
        <CardContent>
          {configEntries.length === 0 ? (
            <p className="text-gray-500">No additional configuration</p>
          ) : (
            <dl className="space-y-3">
              {configEntries.map(([key, value]) => (
                <div key={key} className="border-b pb-2">
                  <dt className="text-sm text-gray-500">{formatLabel(key)}</dt>
                  <dd className="font-medium">
                    {typeof value === 'object' ? (
                      <pre className="text-sm bg-gray-50 p-2 rounded overflow-x-auto">
                        {JSON.stringify(value, null, 2)}
                      </pre>
                    ) : (
                      formatValue(value)
                    )}
                  </dd>
                </div>
              ))}
            </dl>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

interface ExecutionsTabProps {
  executions: JobExecution[]
  loading: boolean
  page: number
  totalPages: number
  onPageChange: (page: number) => void
  selectedExecution: JobExecution | null
  onSelectExecution: (execution: JobExecution | null) => void
}

const ExecutionsTab = ({
  executions,
  loading,
  page,
  totalPages,
  onPageChange,
  selectedExecution,
  onSelectExecution,
}: ExecutionsTabProps) => {
  if (loading) {
    return (
      <div className="flex justify-center py-8">
        <Spinner />
      </div>
    )
  }

  if (executions.length === 0) {
    return (
      <Card>
        <CardContent className="text-center py-8">
          <History className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 font-medium text-gray-900">No executions yet</h3>
          <p className="text-sm text-gray-500 mt-1">
            This job hasn't been executed yet. Click "Run Now" to start the first execution.
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <h3 className="font-semibold">Execution History</h3>
        </CardHeader>
        <CardContent>
          <table className="w-full">
            <thead>
              <tr className="border-b text-left text-sm text-gray-500">
                <th className="pb-3 font-medium">Started</th>
                <th className="pb-3 font-medium">Duration</th>
                <th className="pb-3 font-medium">Status</th>
                <th className="pb-3 font-medium">Server</th>
              </tr>
            </thead>
            <tbody>
              {executions.map((execution) => (
                <tr
                  key={execution.id}
                  onClick={() =>
                    onSelectExecution(
                      selectedExecution?.id === execution.id ? null : execution
                    )
                  }
                  className={`border-b last:border-0 cursor-pointer transition-colors ${
                    selectedExecution?.id === execution.id
                      ? 'bg-blue-50'
                      : 'hover:bg-gray-50'
                  }`}
                >
                  <td className="py-3">
                    {execution.started_at
                      ? new Date(execution.started_at).toLocaleString()
                      : 'Not started'}
                  </td>
                  <td className="py-3">{formatDuration(execution)}</td>
                  <td className="py-3">
                    <ExecutionStatusBadge status={execution.status} />
                  </td>
                  <td className="py-3 text-sm text-gray-600">
                    {execution.server?.name || '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-4 pt-4 border-t">
              <span className="text-sm text-gray-500">
                Page {page + 1} of {totalPages}
              </span>
              <div className="flex gap-2">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => onPageChange(page - 1)}
                  disabled={page === 0}
                >
                  <ChevronLeft className="h-4 w-4" />
                  Previous
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => onPageChange(page + 1)}
                  disabled={page >= totalPages - 1}
                >
                  Next
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Execution Detail Panel */}
      {selectedExecution && (
        <ExecutionDetailPanel
          execution={selectedExecution}
          onClose={() => onSelectExecution(null)}
        />
      )}
    </div>
  )
}

const ExecutionStatusBadge = ({ status }: { status: ExecutionStatus }) => {
  const config: Record<ExecutionStatus, { icon: typeof CheckCircle; color: string; label: string }> =
    {
      success: { icon: CheckCircle, color: 'bg-green-100 text-green-800', label: 'Success' },
      failed: { icon: XCircle, color: 'bg-red-100 text-red-800', label: 'Failed' },
      pending: { icon: Clock, color: 'bg-yellow-100 text-yellow-800', label: 'Pending' },
      running: { icon: Clock, color: 'bg-blue-100 text-blue-800', label: 'Running' },
      cancelled: { icon: XCircle, color: 'bg-gray-100 text-gray-600', label: 'Cancelled' },
    }

  const { icon: Icon, color, label } = config[status]

  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 text-xs rounded-full ${color}`}>
      <Icon className="h-3 w-3" />
      {label}
    </span>
  )
}

const ExecutionDetailPanel = ({
  execution,
  onClose,
}: {
  execution: JobExecution
  onClose: () => void
}) => {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <h3 className="font-semibold">Execution Details</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <XCircle className="h-5 w-5" />
          </button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="grid grid-cols-4 gap-4">
            <div>
              <span className="text-sm text-gray-500">Status</span>
              <div className="mt-1">
                <ExecutionStatusBadge status={execution.status} />
              </div>
            </div>
            <div>
              <span className="text-sm text-gray-500">Started</span>
              <p className="font-medium">
                {execution.started_at
                  ? new Date(execution.started_at).toLocaleString()
                  : 'Not started'}
              </p>
            </div>
            <div>
              <span className="text-sm text-gray-500">Completed</span>
              <p className="font-medium">
                {execution.completed_at
                  ? new Date(execution.completed_at).toLocaleString()
                  : '-'}
              </p>
            </div>
            <div>
              <span className="text-sm text-gray-500">Duration</span>
              <p className="font-medium">{formatDuration(execution)}</p>
            </div>
          </div>

          {execution.error_message && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <h4 className="font-medium text-red-800 mb-2">Error Message</h4>
              <pre className="text-sm text-red-700 whitespace-pre-wrap">
                {execution.error_message}
              </pre>
            </div>
          )}

          {execution.result && Object.keys(execution.result).length > 0 && (
            <div>
              <h4 className="font-medium text-gray-900 mb-2">Result</h4>
              <pre className="bg-gray-50 p-4 rounded-lg text-sm overflow-x-auto">
                {JSON.stringify(execution.result, null, 2)}
              </pre>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

function formatLabel(key: string): string {
  return key
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

function formatValue(value: unknown): string {
  if (typeof value === 'boolean') return value ? 'Yes' : 'No'
  if (value === null || value === undefined) return '-'
  return String(value)
}

function formatDuration(execution: JobExecution): string {
  if (!execution.started_at) return '-'
  const start = new Date(execution.started_at)
  const end = execution.completed_at ? new Date(execution.completed_at) : new Date()
  const durationMs = end.getTime() - start.getTime()

  if (durationMs < 1000) return `${durationMs}ms`
  if (durationMs < 60000) return `${Math.round(durationMs / 1000)}s`
  if (durationMs < 3600000) return `${Math.round(durationMs / 60000)}m`
  return `${Math.round(durationMs / 3600000)}h`
}

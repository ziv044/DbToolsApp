import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { X, ChevronLeft, ChevronRight, Check } from 'lucide-react'
import { Button, Input, Spinner } from '../ui'
import {
  jobService,
  JOB_TYPE_LABELS,
  JOB_TYPE_ICONS,
  SCHEDULE_TYPE_LABELS,
} from '../../services/jobService'
import type { JobType, ScheduleType, CreateJobInput } from '../../services/jobService'
import { policyService } from '../../services/policyService'
import { toast } from '../ui/toastStore'
import { useNavigate } from 'react-router-dom'

interface CreateJobModalProps {
  isOpen: boolean
  onClose: () => void
}

type Step = 'type' | 'schedule' | 'config' | 'review'

const JOB_TYPES: JobType[] = ['policy_execution', 'data_collection', 'custom_script', 'alert_check']
const SCHEDULE_TYPES: ScheduleType[] = ['interval', 'cron', 'once']

const JOB_TYPE_DESCRIPTIONS: Record<JobType, string> = {
  policy_execution: 'Execute a policy on scheduled intervals',
  data_collection: 'Collect metrics and data from servers',
  custom_script: 'Run custom T-SQL scripts',
  alert_check: 'Check for alert conditions',
}

const INTERVAL_PRESETS = [
  { label: 'Every 5 minutes', seconds: 300 },
  { label: 'Every 15 minutes', seconds: 900 },
  { label: 'Every 30 minutes', seconds: 1800 },
  { label: 'Every hour', seconds: 3600 },
  { label: 'Every 6 hours', seconds: 21600 },
  { label: 'Every 12 hours', seconds: 43200 },
  { label: 'Every day', seconds: 86400 },
]

const CRON_TEMPLATES = [
  { label: 'Custom', expression: '', description: 'Enter your own cron expression' },
  { label: 'Every hour', expression: '0 * * * *', description: 'Runs at minute 0 of every hour' },
  { label: 'Daily at midnight', expression: '0 0 * * *', description: 'Runs at 12:00 AM every day' },
  { label: 'Daily at 2 AM', expression: '0 2 * * *', description: 'Runs at 2:00 AM every day' },
  { label: 'Daily at 6 AM', expression: '0 6 * * *', description: 'Runs at 6:00 AM every day' },
  { label: 'Twice daily (6 AM & 6 PM)', expression: '0 6,18 * * *', description: 'Runs at 6:00 AM and 6:00 PM' },
  { label: 'Weekly on Sunday', expression: '0 0 * * 0', description: 'Runs at midnight every Sunday' },
  { label: 'Weekly on Monday', expression: '0 0 * * 1', description: 'Runs at midnight every Monday' },
  { label: 'Monthly on 1st', expression: '0 0 1 * *', description: 'Runs at midnight on the 1st of each month' },
  { label: 'Monthly on 15th', expression: '0 0 15 * *', description: 'Runs at midnight on the 15th of each month' },
]

export const CreateJobModal = ({ isOpen, onClose }: CreateJobModalProps) => {
  const [step, setStep] = useState<Step>('type')
  const [selectedType, setSelectedType] = useState<JobType | null>(null)
  const [name, setName] = useState('')
  const [scheduleType, setScheduleType] = useState<ScheduleType>('interval')
  const [scheduleConfig, setScheduleConfig] = useState<Record<string, unknown>>({
    interval_seconds: 3600,
  })
  const [selectedCronTemplate, setSelectedCronTemplate] = useState<string>('0 2 * * *')
  const [configuration, setConfiguration] = useState<Record<string, unknown>>({})
  const [errors, setErrors] = useState<string[]>([])
  const [runAfterCreate, setRunAfterCreate] = useState(false)
  const queryClient = useQueryClient()
  const navigate = useNavigate()

  // Load policies for policy_execution job type
  const { data: policiesData } = useQuery({
    queryKey: ['policies'],
    queryFn: () => policyService.getAll({}),
    enabled: selectedType === 'policy_execution',
  })

  const createMutation = useMutation({
    mutationFn: async (input: CreateJobInput) => {
      const job = await jobService.create(input)
      // If test run requested, trigger immediate execution
      if (runAfterCreate) {
        try {
          await jobService.runNow(job.id)
        } catch {
          // Don't fail the whole operation if run fails
          toast.warning('Job created but test run failed to start')
        }
      }
      return job
    },
    onSuccess: (job) => {
      if (runAfterCreate) {
        toast.success('Job created and queued for execution')
      } else {
        toast.success('Job created successfully')
      }
      queryClient.invalidateQueries({ queryKey: ['jobs'] })
      handleClose()
      navigate(`/jobs/${job.id}`)
    },
    onError: (error: Error & { response?: { data?: { error?: string } } }) => {
      const message = error.response?.data?.error || 'Failed to create job'
      toast.error(message)
    },
  })

  const handleClose = () => {
    setStep('type')
    setSelectedType(null)
    setName('')
    setScheduleType('interval')
    setScheduleConfig({ interval_seconds: 3600 })
    setSelectedCronTemplate('0 2 * * *')
    setConfiguration({})
    setErrors([])
    setRunAfterCreate(false)
    onClose()
  }

  const handleSelectType = (type: JobType) => {
    setSelectedType(type)
    // Initialize type-specific defaults
    if (type === 'policy_execution') {
      setConfiguration({ policy_id: '' })
    } else if (type === 'custom_script') {
      setConfiguration({ script_content: '', timeout_seconds: 3600 })
    } else {
      setConfiguration({})
    }
    setStep('schedule')
  }

  const handleBack = () => {
    if (step === 'schedule') {
      setStep('type')
      setSelectedType(null)
    } else if (step === 'config') {
      setStep('schedule')
    } else if (step === 'review') {
      setStep('config')
    }
  }

  const handleNext = () => {
    const validationErrors: string[] = []

    if (step === 'schedule') {
      if (!name.trim()) {
        validationErrors.push('Job name is required')
      }
      if (scheduleType === 'cron' && !scheduleConfig.expression) {
        validationErrors.push('Cron expression is required')
      }
      if (scheduleType === 'once' && !scheduleConfig.run_at) {
        validationErrors.push('Run time is required')
      }
      if (scheduleType === 'interval' && !scheduleConfig.interval_seconds) {
        validationErrors.push('Interval is required')
      }
      if (validationErrors.length > 0) {
        setErrors(validationErrors)
        return
      }
      setErrors([])
      setStep('config')
    } else if (step === 'config') {
      if (selectedType === 'policy_execution' && !configuration.policy_id) {
        validationErrors.push('Please select a policy')
      }
      if (selectedType === 'custom_script' && !configuration.script_content) {
        validationErrors.push('Script content is required')
      }
      if (validationErrors.length > 0) {
        setErrors(validationErrors)
        return
      }
      setErrors([])
      setStep('review')
    }
  }

  const handleSave = (isEnabled: boolean) => {
    if (!selectedType) return

    createMutation.mutate({
      name: name.trim(),
      type: selectedType,
      schedule_type: scheduleType,
      schedule_config: scheduleConfig,
      configuration,
      is_enabled: isEnabled,
    })
  }

  const handleScheduleTypeChange = (type: ScheduleType) => {
    setScheduleType(type)
    // Reset schedule config based on type
    if (type === 'interval') {
      setScheduleConfig({ interval_seconds: 3600 })
    } else if (type === 'cron') {
      // Use the default template
      setSelectedCronTemplate('0 2 * * *')
      setScheduleConfig({ expression: '0 2 * * *' })
    } else if (type === 'once') {
      setScheduleConfig({ run_at: '' })
    }
  }

  const handleCronTemplateChange = (expression: string) => {
    setSelectedCronTemplate(expression)
    if (expression) {
      setScheduleConfig({ expression })
    }
  }

  if (!isOpen) return null

  const policies = policiesData?.policies ?? []

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black bg-opacity-50" onClick={handleClose} />

      {/* Modal */}
      <div className="relative bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <h2 className="text-xl font-semibold">
            {step === 'type' && 'Select Job Type'}
            {step === 'schedule' && 'Configure Schedule'}
            {step === 'config' && 'Job Configuration'}
            {step === 'review' && 'Review Job'}
          </h2>
          <button onClick={handleClose} className="text-gray-400 hover:text-gray-600">
            <X className="h-6 w-6" />
          </button>
        </div>

        {/* Step indicator */}
        <div className="flex items-center justify-center gap-2 py-4 border-b bg-gray-50">
          {['type', 'schedule', 'config', 'review'].map((s, i) => (
            <div key={s} className="flex items-center">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium
                  ${step === s ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-600'}
                  ${['type', 'schedule', 'config', 'review'].indexOf(step) > i ? 'bg-green-500 text-white' : ''}`}
              >
                {['type', 'schedule', 'config', 'review'].indexOf(step) > i ? (
                  <Check className="h-4 w-4" />
                ) : (
                  i + 1
                )}
              </div>
              {i < 3 && <div className="w-12 h-0.5 bg-gray-200 mx-1" />}
            </div>
          ))}
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-200px)]">
          {/* Step 1: Type Selection */}
          {step === 'type' && (
            <div className="grid grid-cols-2 gap-4">
              {JOB_TYPES.map((type) => (
                <button
                  key={type}
                  onClick={() => handleSelectType(type)}
                  className="p-4 border rounded-lg text-left hover:border-blue-500 hover:bg-blue-50 transition-colors"
                >
                  <div className="text-3xl mb-2">{JOB_TYPE_ICONS[type]}</div>
                  <h3 className="font-medium text-gray-900">{JOB_TYPE_LABELS[type]}</h3>
                  <p className="text-sm text-gray-500 mt-1">{JOB_TYPE_DESCRIPTIONS[type]}</p>
                </button>
              ))}
            </div>
          )}

          {/* Step 2: Schedule Configuration */}
          {step === 'schedule' && (
            <div className="space-y-4">
              {errors.length > 0 && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <ul className="list-disc list-inside text-red-700 text-sm">
                    {errors.map((error, i) => (
                      <li key={i}>{error}</li>
                    ))}
                  </ul>
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Job Name <span className="text-red-500">*</span>
                </label>
                <Input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g., Nightly Backup"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Schedule Type <span className="text-red-500">*</span>
                </label>
                <div className="flex gap-2">
                  {SCHEDULE_TYPES.map((type) => (
                    <button
                      key={type}
                      onClick={() => handleScheduleTypeChange(type)}
                      className={`px-4 py-2 rounded-lg border text-sm font-medium transition-colors
                        ${scheduleType === type
                          ? 'bg-blue-600 text-white border-blue-600'
                          : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'}`}
                    >
                      {SCHEDULE_TYPE_LABELS[type]}
                    </button>
                  ))}
                </div>
              </div>

              {/* Schedule config based on type */}
              {scheduleType === 'interval' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Interval <span className="text-red-500">*</span>
                  </label>
                  <select
                    value={scheduleConfig.interval_seconds as number}
                    onChange={(e) =>
                      setScheduleConfig({ interval_seconds: Number(e.target.value) })
                    }
                    className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {INTERVAL_PRESETS.map((preset) => (
                      <option key={preset.seconds} value={preset.seconds}>
                        {preset.label}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {scheduleType === 'cron' && (
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Schedule Template
                    </label>
                    <select
                      value={selectedCronTemplate}
                      onChange={(e) => handleCronTemplateChange(e.target.value)}
                      className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      {CRON_TEMPLATES.map((template) => (
                        <option key={template.label} value={template.expression}>
                          {template.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Cron Expression <span className="text-red-500">*</span>
                    </label>
                    <Input
                      value={(scheduleConfig.expression as string) || ''}
                      onChange={(e) => {
                        setScheduleConfig({ expression: e.target.value })
                        // Set to custom if expression doesn't match any template
                        const matchingTemplate = CRON_TEMPLATES.find(
                          (t) => t.expression === e.target.value
                        )
                        if (!matchingTemplate) {
                          setSelectedCronTemplate('')
                        }
                      }}
                      placeholder="e.g., 0 2 * * *"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      Format: minute hour day-of-month month day-of-week
                    </p>
                  </div>

                  {/* Human-readable preview */}
                  {typeof scheduleConfig.expression === 'string' && scheduleConfig.expression && (
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                      <p className="text-sm text-blue-800">
                        <strong>Runs at:</strong> {describeCron(scheduleConfig.expression)}
                      </p>
                    </div>
                  )}
                </div>
              )}

              {scheduleType === 'once' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Run At <span className="text-red-500">*</span>
                  </label>
                  <Input
                    type="datetime-local"
                    value={(scheduleConfig.run_at as string) || ''}
                    onChange={(e) => setScheduleConfig({ run_at: e.target.value })}
                  />
                </div>
              )}
            </div>
          )}

          {/* Step 3: Job Configuration */}
          {step === 'config' && selectedType && (
            <div className="space-y-4">
              {errors.length > 0 && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <ul className="list-disc list-inside text-red-700 text-sm">
                    {errors.map((error, i) => (
                      <li key={i}>{error}</li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="bg-blue-50 rounded-lg p-4">
                <p className="text-sm text-blue-800">
                  <span className="text-xl mr-2">{JOB_TYPE_ICONS[selectedType]}</span>
                  Configuring <strong>{JOB_TYPE_LABELS[selectedType]}</strong> job
                </p>
              </div>

              {selectedType === 'policy_execution' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Select Policy <span className="text-red-500">*</span>
                  </label>
                  <select
                    value={(configuration.policy_id as string) || ''}
                    onChange={(e) =>
                      setConfiguration({ ...configuration, policy_id: e.target.value })
                    }
                    className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Select a policy...</option>
                    {policies.map((policy) => (
                      <option key={policy.id} value={policy.id}>
                        {policy.name}
                      </option>
                    ))}
                  </select>
                  {policies.length === 0 && (
                    <p className="text-sm text-gray-500 mt-1">
                      No policies found. Create a policy first.
                    </p>
                  )}
                </div>
              )}

              {selectedType === 'custom_script' && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      T-SQL Script <span className="text-red-500">*</span>
                    </label>
                    <textarea
                      value={(configuration.script_content as string) || ''}
                      onChange={(e) =>
                        setConfiguration({ ...configuration, script_content: e.target.value })
                      }
                      placeholder="-- Enter your T-SQL script here"
                      className="w-full px-3 py-2 border rounded-lg text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500"
                      rows={8}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Timeout (seconds)
                    </label>
                    <Input
                      type="number"
                      value={(configuration.timeout_seconds as number) || 3600}
                      onChange={(e) =>
                        setConfiguration({
                          ...configuration,
                          timeout_seconds: Number(e.target.value),
                        })
                      }
                    />
                  </div>
                </>
              )}

              {selectedType === 'data_collection' && (
                <div className="bg-gray-50 rounded-lg p-4">
                  <p className="text-sm text-gray-600">
                    Data collection jobs will gather metrics from all servers in the target groups.
                    No additional configuration required.
                  </p>
                </div>
              )}

              {selectedType === 'alert_check' && (
                <div className="bg-gray-50 rounded-lg p-4">
                  <p className="text-sm text-gray-600">
                    Alert check jobs will evaluate alert conditions across all servers.
                    No additional configuration required.
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Step 4: Review */}
          {step === 'review' && selectedType && (
            <div className="space-y-4">
              <div className="bg-gray-50 rounded-lg p-4 space-y-3">
                <div>
                  <span className="text-sm text-gray-500">Name</span>
                  <p className="font-medium">{name}</p>
                </div>
                <div>
                  <span className="text-sm text-gray-500">Type</span>
                  <p className="font-medium">
                    {JOB_TYPE_ICONS[selectedType]} {JOB_TYPE_LABELS[selectedType]}
                  </p>
                </div>
                <div>
                  <span className="text-sm text-gray-500">Schedule</span>
                  <p className="font-medium">
                    {SCHEDULE_TYPE_LABELS[scheduleType]}
                    {scheduleType === 'interval' &&
                      ` (${formatInterval(scheduleConfig.interval_seconds as number)})`}
                    {scheduleType === 'cron' && `: ${scheduleConfig.expression as string}`}
                    {scheduleType === 'once' &&
                      `: ${new Date(scheduleConfig.run_at as string).toLocaleString()}`}
                  </p>
                </div>
                {Object.keys(configuration).length > 0 && (
                  <div>
                    <span className="text-sm text-gray-500">Configuration</span>
                    <pre className="mt-1 p-2 bg-white rounded border text-sm overflow-x-auto">
                      {JSON.stringify(configuration, null, 2)}
                    </pre>
                  </div>
                )}
              </div>

              {/* Test Run Option */}
              <div className="flex items-center gap-2 p-4 bg-blue-50 rounded-lg border border-blue-200">
                <input
                  type="checkbox"
                  id="runAfterCreate"
                  checked={runAfterCreate}
                  onChange={(e) => setRunAfterCreate(e.target.checked)}
                  className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <label htmlFor="runAfterCreate" className="text-sm text-blue-800">
                  <strong>Test Run:</strong> Execute this job immediately after creation
                </label>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-4 border-t bg-gray-50">
          <div>
            {step !== 'type' && (
              <Button variant="ghost" onClick={handleBack}>
                <ChevronLeft className="h-4 w-4 mr-1" />
                Back
              </Button>
            )}
          </div>
          <div className="flex gap-2">
            {(step === 'schedule' || step === 'config') && (
              <Button onClick={handleNext}>
                Next
                <ChevronRight className="h-4 w-4 ml-1" />
              </Button>
            )}
            {step === 'review' && (
              <>
                <Button
                  variant="secondary"
                  onClick={() => handleSave(false)}
                  disabled={createMutation.isPending}
                >
                  {createMutation.isPending && <Spinner size="sm" className="mr-2" />}
                  Save as Disabled
                </Button>
                <Button onClick={() => handleSave(true)} disabled={createMutation.isPending}>
                  {createMutation.isPending && <Spinner size="sm" className="mr-2" />}
                  Save & Enable
                </Button>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

function formatInterval(seconds: number): string {
  if (seconds >= 86400) return `every ${Math.floor(seconds / 86400)} day(s)`
  if (seconds >= 3600) return `every ${Math.floor(seconds / 3600)} hour(s)`
  if (seconds >= 60) return `every ${Math.floor(seconds / 60)} minute(s)`
  return `every ${seconds} seconds`
}

/**
 * Generate a human-readable description of a cron expression.
 * This is a simplified version - for full support, consider using cronstrue library.
 */
function describeCron(expression: string): string {
  const parts = expression.trim().split(/\s+/)
  if (parts.length !== 5) return expression

  const [minute, hour, dayOfMonth, month, dayOfWeek] = parts

  // Check for known patterns
  const template = CRON_TEMPLATES.find((t) => t.expression === expression)
  if (template && template.description) {
    return template.description
  }

  // Build description for common patterns
  const descriptions: string[] = []

  // Time
  if (minute !== '*' && hour !== '*') {
    const h = parseInt(hour, 10)
    const m = parseInt(minute, 10)
    const period = h >= 12 ? 'PM' : 'AM'
    const displayHour = h > 12 ? h - 12 : h === 0 ? 12 : h
    descriptions.push(`${displayHour}:${m.toString().padStart(2, '0')} ${period}`)
  } else if (hour !== '*') {
    const h = parseInt(hour, 10)
    const period = h >= 12 ? 'PM' : 'AM'
    const displayHour = h > 12 ? h - 12 : h === 0 ? 12 : h
    descriptions.push(`${displayHour}:00 ${period}`)
  } else if (minute === '0') {
    descriptions.push('at the start of every hour')
  }

  // Day of week
  const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
  if (dayOfWeek !== '*') {
    const days = dayOfWeek.split(',').map((d) => dayNames[parseInt(d, 10)] || d)
    descriptions.push(`every ${days.join(', ')}`)
  }

  // Day of month
  if (dayOfMonth !== '*') {
    const ordinal = (n: number) => {
      const s = ['th', 'st', 'nd', 'rd']
      const v = n % 100
      return n + (s[(v - 20) % 10] || s[v] || s[0])
    }
    descriptions.push(`on the ${ordinal(parseInt(dayOfMonth, 10))}`)
  }

  // Month
  const monthNames = ['', 'January', 'February', 'March', 'April', 'May', 'June',
                      'July', 'August', 'September', 'October', 'November', 'December']
  if (month !== '*') {
    const months = month.split(',').map((m) => monthNames[parseInt(m, 10)] || m)
    descriptions.push(`in ${months.join(', ')}`)
  }

  if (descriptions.length === 0) {
    return expression
  }

  return descriptions.join(' ')
}

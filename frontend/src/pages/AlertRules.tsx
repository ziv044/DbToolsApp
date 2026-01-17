import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import {
  Plus,
  Pencil,
  Trash2,
  RefreshCw,
  Bell,
  AlertTriangle,
  AlertCircle,
  Info,
  Power,
  Eye,
  ArrowLeft,
  X,
} from 'lucide-react'
import { Card, CardHeader, CardContent, Button, Spinner } from '../components/ui'
import {
  alertService,
  SEVERITY_LABELS,
  SEVERITY_COLORS,
  OPERATOR_LABELS,
  METRIC_TYPE_LABELS,
} from '../services/alertService'
import type { AlertRule, AlertSeverity, AlertOperator, CreateRuleInput } from '../services/alertService'
import { toast } from '../components/ui/toastStore'

// Rule templates for quick creation
const RULE_TEMPLATES: Omit<CreateRuleInput, 'name'>[] = [
  { metric_type: 'cpu_percent', operator: 'gt', threshold: 90, severity: 'critical' },
  { metric_type: 'memory_percent', operator: 'gt', threshold: 90, severity: 'critical' },
  { metric_type: 'connection_count', operator: 'gt', threshold: 200, severity: 'warning' },
  { metric_type: 'blocked_processes', operator: 'gt', threshold: 5, severity: 'warning' },
  { metric_type: 'page_life_expectancy', operator: 'lt', threshold: 300, severity: 'warning' },
]

const TEMPLATE_NAMES: Record<string, string> = {
  cpu_percent: 'High CPU',
  memory_percent: 'High Memory',
  connection_count: 'Connection Spike',
  blocked_processes: 'Blocked Processes',
  page_life_expectancy: 'Low Page Life',
}

const METRIC_OPTIONS = [
  { value: 'cpu_percent', label: 'CPU %' },
  { value: 'memory_percent', label: 'Memory %' },
  { value: 'connection_count', label: 'Connections' },
  { value: 'batch_requests_sec', label: 'Batch Req/s' },
  { value: 'page_life_expectancy', label: 'Page Life Expectancy' },
  { value: 'blocked_processes', label: 'Blocked Processes' },
]

const OPERATOR_OPTIONS: { value: AlertOperator; label: string }[] = [
  { value: 'gt', label: 'Greater than (>)' },
  { value: 'gte', label: 'Greater or equal (>=)' },
  { value: 'lt', label: 'Less than (<)' },
  { value: 'lte', label: 'Less or equal (<=)' },
  { value: 'eq', label: 'Equal to (=)' },
]

const SEVERITY_OPTIONS: { value: AlertSeverity; label: string }[] = [
  { value: 'info', label: 'Info' },
  { value: 'warning', label: 'Warning' },
  { value: 'critical', label: 'Critical' },
]

export const AlertRules = () => {
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
  const [editingRule, setEditingRule] = useState<AlertRule | null>(null)
  const [selectedTemplate, setSelectedTemplate] = useState<Omit<CreateRuleInput, 'name'> | null>(null)
  const [isTabVisible, setIsTabVisible] = useState(!document.hidden)
  const queryClient = useQueryClient()

  // Handle visibility change
  useEffect(() => {
    const handleVisibilityChange = () => {
      const visible = !document.hidden
      setIsTabVisible(visible)
      if (visible) {
        queryClient.invalidateQueries({ queryKey: ['alert-rules'] })
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange)
  }, [queryClient])

  const { data, isLoading, refetch, isFetching } = useQuery({
    queryKey: ['alert-rules'],
    queryFn: () => alertService.getRules({ limit: 100 }),
    refetchInterval: isTabVisible ? 30_000 : false,
  })

  const enableMutation = useMutation({
    mutationFn: (ruleId: string) => alertService.enableRule(ruleId),
    onSuccess: () => {
      toast.success('Rule enabled')
      queryClient.invalidateQueries({ queryKey: ['alert-rules'] })
    },
    onError: () => toast.error('Failed to enable rule'),
  })

  const disableMutation = useMutation({
    mutationFn: (ruleId: string) => alertService.disableRule(ruleId),
    onSuccess: () => {
      toast.success('Rule disabled')
      queryClient.invalidateQueries({ queryKey: ['alert-rules'] })
    },
    onError: () => toast.error('Failed to disable rule'),
  })

  const deleteMutation = useMutation({
    mutationFn: (ruleId: string) => alertService.deleteRule(ruleId),
    onSuccess: () => {
      toast.success('Rule deleted')
      queryClient.invalidateQueries({ queryKey: ['alert-rules'] })
    },
    onError: () => toast.error('Failed to delete rule'),
  })

  const handleDelete = (rule: AlertRule) => {
    if (window.confirm(`Delete rule "${rule.name}"? This will also delete all associated alerts.`)) {
      deleteMutation.mutate(rule.id)
    }
  }

  const handleToggleEnabled = (rule: AlertRule) => {
    if (rule.is_enabled) {
      disableMutation.mutate(rule.id)
    } else {
      enableMutation.mutate(rule.id)
    }
  }

  const handleTemplateClick = (template: Omit<CreateRuleInput, 'name'>) => {
    setSelectedTemplate(template)
    setEditingRule(null)
    setIsCreateModalOpen(true)
  }

  const rules = data?.rules ?? []

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link to="/alerts" className="text-gray-500 hover:text-gray-700">
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <h1 className="text-2xl font-bold text-gray-900">Alert Rules</h1>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={() => refetch()} disabled={isFetching}>
            <RefreshCw className={`h-4 w-4 mr-2 ${isFetching ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button onClick={() => {
            setSelectedTemplate(null)
            setEditingRule(null)
            setIsCreateModalOpen(true)
          }}>
            <Plus className="h-4 w-4 mr-2" />
            Create Rule
          </Button>
        </div>
      </div>

      {/* Templates Section */}
      <Card>
        <CardHeader>
          <h2 className="text-lg font-semibold">Quick Templates</h2>
          <p className="text-sm text-gray-500 mt-1">
            Click a template to quickly create a common alert rule
          </p>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {RULE_TEMPLATES.map((template) => (
              <button
                key={template.metric_type}
                onClick={() => handleTemplateClick(template)}
                className="inline-flex items-center gap-2 px-3 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm transition-colors"
              >
                <SeverityIcon severity={template.severity} />
                {TEMPLATE_NAMES[template.metric_type] || template.metric_type}
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Rules List */}
      <Card>
        <CardHeader>
          <h2 className="text-lg font-semibold">All Rules</h2>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Spinner size="lg" />
            </div>
          ) : rules.length === 0 ? (
            <div className="text-center py-12">
              <Bell className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No alert rules</h3>
              <p className="mt-1 text-sm text-gray-500">
                Create your first alert rule to start monitoring.
              </p>
              <div className="mt-6">
                <Button onClick={() => {
                  setSelectedTemplate(null)
                  setEditingRule(null)
                  setIsCreateModalOpen(true)
                }}>
                  <Plus className="h-4 w-4 mr-2" />
                  Create Rule
                </Button>
              </div>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b text-left text-sm text-gray-500">
                    <th className="pb-3 font-medium">Name</th>
                    <th className="pb-3 font-medium">Metric</th>
                    <th className="pb-3 font-medium">Condition</th>
                    <th className="pb-3 font-medium">Severity</th>
                    <th className="pb-3 font-medium">Status</th>
                    <th className="pb-3 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {rules.map((rule) => (
                    <RuleRow
                      key={rule.id}
                      rule={rule}
                      onEdit={() => {
                        setSelectedTemplate(null)
                        setEditingRule(rule)
                      }}
                      onDelete={() => handleDelete(rule)}
                      onToggle={() => handleToggleEnabled(rule)}
                    />
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Create/Edit Modal */}
      {(isCreateModalOpen || editingRule) && (
        <RuleFormModal
          rule={editingRule}
          template={selectedTemplate}
          onClose={() => {
            setIsCreateModalOpen(false)
            setEditingRule(null)
            setSelectedTemplate(null)
          }}
        />
      )}
    </div>
  )
}

interface RuleRowProps {
  rule: AlertRule
  onEdit: () => void
  onDelete: () => void
  onToggle: () => void
}

const RuleRow = ({ rule, onEdit, onDelete, onToggle }: RuleRowProps) => {
  return (
    <tr className="border-b last:border-0 hover:bg-gray-50">
      <td className="py-3">
        <span className="font-medium">{rule.name}</span>
      </td>
      <td className="py-3 text-sm text-gray-600">
        {METRIC_TYPE_LABELS[rule.metric_type] || rule.metric_type}
      </td>
      <td className="py-3 text-sm">
        <code className="px-2 py-1 bg-gray-100 rounded">
          {OPERATOR_LABELS[rule.operator]} {rule.threshold}
        </code>
      </td>
      <td className="py-3">
        <SeverityBadge severity={rule.severity} />
      </td>
      <td className="py-3">
        <button
          onClick={onToggle}
          className={`inline-flex items-center gap-1 px-2 py-0.5 text-xs rounded-full transition-colors ${
            rule.is_enabled
              ? 'bg-green-100 text-green-800 hover:bg-green-200'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
        >
          <Power className="h-3 w-3" />
          {rule.is_enabled ? 'Enabled' : 'Disabled'}
        </button>
      </td>
      <td className="py-3">
        <div className="flex items-center gap-1">
          <button
            onClick={onEdit}
            className="p-1.5 text-blue-600 hover:bg-blue-50 rounded"
            title="Edit"
          >
            <Pencil className="h-4 w-4" />
          </button>
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

interface SeverityBadgeProps {
  severity: AlertSeverity
}

const SeverityBadge = ({ severity }: SeverityBadgeProps) => {
  const colors = SEVERITY_COLORS[severity]

  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 text-xs rounded-full ${colors.bg} ${colors.text}`}
    >
      <SeverityIcon severity={severity} className="h-3 w-3" />
      {SEVERITY_LABELS[severity]}
    </span>
  )
}

interface SeverityIconProps {
  severity: AlertSeverity
  className?: string
}

const SeverityIcon = ({ severity, className = 'h-4 w-4' }: SeverityIconProps) => {
  const colors = SEVERITY_COLORS[severity]
  switch (severity) {
    case 'critical':
      return <AlertCircle className={`${className} ${colors.icon}`} />
    case 'warning':
      return <AlertTriangle className={`${className} ${colors.icon}`} />
    default:
      return <Info className={`${className} ${colors.icon}`} />
  }
}

interface RuleFormModalProps {
  rule: AlertRule | null
  template: Omit<CreateRuleInput, 'name'> | null
  onClose: () => void
}

const RuleFormModal = ({ rule, template, onClose }: RuleFormModalProps) => {
  const queryClient = useQueryClient()
  const isEditing = !!rule

  const [formData, setFormData] = useState<CreateRuleInput>(() => {
    if (rule) {
      return {
        name: rule.name,
        metric_type: rule.metric_type,
        operator: rule.operator,
        threshold: rule.threshold,
        severity: rule.severity,
        is_enabled: rule.is_enabled,
      }
    }
    if (template) {
      return {
        name: TEMPLATE_NAMES[template.metric_type] || '',
        ...template,
        is_enabled: true,
      }
    }
    return {
      name: '',
      metric_type: 'cpu_percent',
      operator: 'gt',
      threshold: 90,
      severity: 'warning',
      is_enabled: true,
    }
  })

  const [errors, setErrors] = useState<Record<string, string>>({})

  const createMutation = useMutation({
    mutationFn: (input: CreateRuleInput) => alertService.createRule(input),
    onSuccess: () => {
      toast.success('Rule created')
      queryClient.invalidateQueries({ queryKey: ['alert-rules'] })
      onClose()
    },
    onError: () => toast.error('Failed to create rule'),
  })

  const updateMutation = useMutation({
    mutationFn: (input: CreateRuleInput) => alertService.updateRule(rule!.id, input),
    onSuccess: () => {
      toast.success('Rule updated')
      queryClient.invalidateQueries({ queryKey: ['alert-rules'] })
      onClose()
    },
    onError: () => toast.error('Failed to update rule'),
  })

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {}

    if (!formData.name.trim()) {
      newErrors.name = 'Name is required'
    }

    if (formData.threshold <= 0) {
      newErrors.threshold = 'Threshold must be a positive number'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    if (!validate()) {
      return
    }

    if (isEditing) {
      updateMutation.mutate(formData)
    } else {
      createMutation.mutate(formData)
    }
  }

  const applyTemplate = (tpl: Omit<CreateRuleInput, 'name'>) => {
    setFormData({
      ...formData,
      ...tpl,
      name: TEMPLATE_NAMES[tpl.metric_type] || formData.name,
    })
  }

  const isPending = createMutation.isPending || updateMutation.isPending

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-lg w-full mx-4 max-h-[80vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold">
              {isEditing ? 'Edit Alert Rule' : 'Create Alert Rule'}
            </h2>
            <button
              onClick={onClose}
              className="p-1 text-gray-400 hover:text-gray-600 rounded"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Templates (only for create) */}
          {!isEditing && (
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Quick Templates
              </label>
              <div className="flex flex-wrap gap-2">
                {RULE_TEMPLATES.map((tpl) => (
                  <button
                    key={tpl.metric_type}
                    type="button"
                    onClick={() => applyTemplate(tpl)}
                    className="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded transition-colors"
                  >
                    {TEMPLATE_NAMES[tpl.metric_type]}
                  </button>
                ))}
              </div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Name */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Rule Name *
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  errors.name ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="e.g., High CPU Alert"
              />
              {errors.name && (
                <p className="mt-1 text-sm text-red-500">{errors.name}</p>
              )}
            </div>

            {/* Metric */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Metric
              </label>
              <select
                value={formData.metric_type}
                onChange={(e) => setFormData({ ...formData, metric_type: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {METRIC_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Condition */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Operator
                </label>
                <select
                  value={formData.operator}
                  onChange={(e) =>
                    setFormData({ ...formData, operator: e.target.value as AlertOperator })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {OPERATOR_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Threshold *
                </label>
                <input
                  type="number"
                  value={formData.threshold}
                  onChange={(e) =>
                    setFormData({ ...formData, threshold: parseFloat(e.target.value) || 0 })
                  }
                  className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    errors.threshold ? 'border-red-500' : 'border-gray-300'
                  }`}
                  min="0"
                  step="0.01"
                />
                {errors.threshold && (
                  <p className="mt-1 text-sm text-red-500">{errors.threshold}</p>
                )}
              </div>
            </div>

            {/* Severity */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Severity
              </label>
              <select
                value={formData.severity}
                onChange={(e) =>
                  setFormData({ ...formData, severity: e.target.value as AlertSeverity })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {SEVERITY_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Enabled */}
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="is_enabled"
                checked={formData.is_enabled}
                onChange={(e) => setFormData({ ...formData, is_enabled: e.target.checked })}
                className="rounded border-gray-300"
              />
              <label htmlFor="is_enabled" className="text-sm text-gray-700">
                Enable rule immediately
              </label>
            </div>

            {/* Preview */}
            <div className="p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
                <Eye className="h-4 w-4" />
                Rule Preview
              </div>
              <p className="text-sm text-gray-600">
                Alert will trigger when{' '}
                <strong>{METRIC_TYPE_LABELS[formData.metric_type] || formData.metric_type}</strong>{' '}
                is{' '}
                <strong>
                  {OPERATOR_OPTIONS.find((o) => o.value === formData.operator)?.label.toLowerCase()}{' '}
                  {formData.threshold}
                </strong>
              </p>
              <div className="mt-2">
                <SeverityBadge severity={formData.severity} />
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-2 pt-4">
              <Button type="button" variant="secondary" onClick={onClose} className="flex-1">
                Cancel
              </Button>
              <Button type="submit" disabled={isPending} className="flex-1">
                {isPending ? (
                  <>
                    <Spinner size="sm" className="mr-2" />
                    {isEditing ? 'Updating...' : 'Creating...'}
                  </>
                ) : isEditing ? (
                  'Update Rule'
                ) : (
                  'Create Rule'
                )}
              </Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}

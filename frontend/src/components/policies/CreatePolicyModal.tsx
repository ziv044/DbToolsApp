import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { X, ChevronLeft, ChevronRight, Check } from 'lucide-react'
import { Button, Input, Spinner } from '../ui'
import {
  policyService,
  POLICY_TYPE_LABELS,
  POLICY_TYPE_DESCRIPTIONS,
  POLICY_TYPE_ICONS,
} from '../../services/policyService'
import type { PolicyType, CreatePolicyInput, PolicySchema } from '../../services/policyService'
import { toast } from '../ui/toastStore'
import { useNavigate } from 'react-router-dom'

interface CreatePolicyModalProps {
  isOpen: boolean
  onClose: () => void
}

type Step = 'type' | 'details' | 'review'

const POLICY_TYPES: PolicyType[] = ['backup', 'index_maintenance', 'integrity_check', 'custom_script']

// Default schemas for when API is not available
const DEFAULT_SCHEMAS: Record<PolicyType, PolicySchema> = {
  backup: {
    required: ['backup_type', 'destination_path'],
    optional: ['compression', 'retention_days', 'verify_backup', 'copy_only'],
    defaults: { compression: true, retention_days: 7, verify_backup: true, copy_only: false },
    valid_values: { backup_type: ['full', 'differential', 'log'] },
  },
  index_maintenance: {
    required: [],
    optional: ['fragmentation_threshold', 'rebuild_threshold', 'include_statistics', 'max_dop', 'online'],
    defaults: { fragmentation_threshold: 10, rebuild_threshold: 30, include_statistics: true, max_dop: 0, online: true },
  },
  integrity_check: {
    required: [],
    optional: ['check_type', 'include_indexes', 'include_extended_logical_checks', 'max_dop'],
    defaults: { check_type: 'physical', include_indexes: true, include_extended_logical_checks: false, max_dop: 0 },
    valid_values: { check_type: ['physical', 'logical', 'both'] },
  },
  custom_script: {
    required: ['script_content'],
    optional: ['timeout_seconds', 'run_as_user'],
    defaults: { timeout_seconds: 3600 },
  },
}

const FIELD_LABELS: Record<string, string> = {
  backup_type: 'Backup Type',
  destination_path: 'Destination Path',
  compression: 'Enable Compression',
  retention_days: 'Retention Days',
  verify_backup: 'Verify Backup',
  copy_only: 'Copy Only',
  fragmentation_threshold: 'Fragmentation Threshold (%)',
  rebuild_threshold: 'Rebuild Threshold (%)',
  include_statistics: 'Update Statistics',
  max_dop: 'Max Degree of Parallelism',
  online: 'Online Operations',
  check_type: 'Check Type',
  include_indexes: 'Include Indexes',
  include_extended_logical_checks: 'Extended Logical Checks',
  script_content: 'T-SQL Script',
  timeout_seconds: 'Timeout (seconds)',
  run_as_user: 'Run As User',
}

export const CreatePolicyModal = ({ isOpen, onClose }: CreatePolicyModalProps) => {
  const [step, setStep] = useState<Step>('type')
  const [selectedType, setSelectedType] = useState<PolicyType | null>(null)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [configuration, setConfiguration] = useState<Record<string, unknown>>({})
  const [errors, setErrors] = useState<string[]>([])
  const queryClient = useQueryClient()
  const navigate = useNavigate()

  const createMutation = useMutation({
    mutationFn: (input: CreatePolicyInput) => policyService.create(input),
    onSuccess: (policy) => {
      toast.success('Policy created successfully')
      queryClient.invalidateQueries({ queryKey: ['policies'] })
      handleClose()
      navigate(`/policies/${policy.id}`)
    },
    onError: (error: Error & { response?: { data?: { details?: string[] } } }) => {
      const details = error.response?.data?.details
      if (details) {
        setErrors(details)
      } else {
        toast.error('Failed to create policy')
      }
    },
  })

  const handleClose = () => {
    setStep('type')
    setSelectedType(null)
    setName('')
    setDescription('')
    setConfiguration({})
    setErrors([])
    onClose()
  }

  const handleSelectType = (type: PolicyType) => {
    setSelectedType(type)
    // Initialize with defaults
    const schema = DEFAULT_SCHEMAS[type]
    setConfiguration({ ...schema.defaults })
    setStep('details')
  }

  const handleBack = () => {
    if (step === 'details') {
      setStep('type')
      setSelectedType(null)
    } else if (step === 'review') {
      setStep('details')
    }
  }

  const handleNext = () => {
    if (step === 'details') {
      // Validate
      const validationErrors: string[] = []
      if (!name.trim()) {
        validationErrors.push('Name is required')
      }
      if (selectedType) {
        const schema = DEFAULT_SCHEMAS[selectedType]
        for (const field of schema.required) {
          if (!configuration[field]) {
            validationErrors.push(`${FIELD_LABELS[field] || field} is required`)
          }
        }
      }
      if (validationErrors.length > 0) {
        setErrors(validationErrors)
        return
      }
      setErrors([])
      setStep('review')
    }
  }

  const handleSave = (isActive: boolean) => {
    if (!selectedType) return

    createMutation.mutate({
      name: name.trim(),
      type: selectedType,
      description: description.trim() || undefined,
      configuration,
      is_active: isActive,
    })
  }

  const handleConfigChange = (field: string, value: unknown) => {
    setConfiguration((prev) => ({ ...prev, [field]: value }))
  }

  if (!isOpen) return null

  const schema = selectedType ? DEFAULT_SCHEMAS[selectedType] : null
  const allFields = schema ? [...schema.required, ...schema.optional] : []

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black bg-opacity-50" onClick={handleClose} />

      {/* Modal */}
      <div className="relative bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <h2 className="text-xl font-semibold">
            {step === 'type' && 'Select Policy Type'}
            {step === 'details' && 'Configure Policy'}
            {step === 'review' && 'Review Policy'}
          </h2>
          <button onClick={handleClose} className="text-gray-400 hover:text-gray-600">
            <X className="h-6 w-6" />
          </button>
        </div>

        {/* Step indicator */}
        <div className="flex items-center justify-center gap-2 py-4 border-b bg-gray-50">
          {['type', 'details', 'review'].map((s, i) => (
            <div key={s} className="flex items-center">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium
                  ${step === s ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-600'}
                  ${['type', 'details', 'review'].indexOf(step) > i ? 'bg-green-500 text-white' : ''}`}
              >
                {['type', 'details', 'review'].indexOf(step) > i ? (
                  <Check className="h-4 w-4" />
                ) : (
                  i + 1
                )}
              </div>
              {i < 2 && <div className="w-12 h-0.5 bg-gray-200 mx-1" />}
            </div>
          ))}
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-200px)]">
          {/* Step 1: Type Selection */}
          {step === 'type' && (
            <div className="grid grid-cols-2 gap-4">
              {POLICY_TYPES.map((type) => (
                <button
                  key={type}
                  onClick={() => handleSelectType(type)}
                  className="p-4 border rounded-lg text-left hover:border-blue-500 hover:bg-blue-50 transition-colors"
                >
                  <div className="text-3xl mb-2">{POLICY_TYPE_ICONS[type]}</div>
                  <h3 className="font-medium text-gray-900">{POLICY_TYPE_LABELS[type]}</h3>
                  <p className="text-sm text-gray-500 mt-1">{POLICY_TYPE_DESCRIPTIONS[type]}</p>
                </button>
              ))}
            </div>
          )}

          {/* Step 2: Details */}
          {step === 'details' && selectedType && schema && (
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
                  Policy Name <span className="text-red-500">*</span>
                </label>
                <Input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g., Daily Full Backup"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Optional description..."
                  className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows={2}
                />
              </div>

              <div className="border-t pt-4">
                <h3 className="font-medium text-gray-900 mb-3">
                  {POLICY_TYPE_LABELS[selectedType]} Configuration
                </h3>

                <div className="space-y-4">
                  {allFields.map((field) => {
                    const isRequired = schema.required.includes(field)
                    const validValues = schema.valid_values?.[field]
                    const value = configuration[field]

                    // Render different input types based on field
                    if (validValues) {
                      return (
                        <div key={field}>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            {FIELD_LABELS[field] || field}
                            {isRequired && <span className="text-red-500"> *</span>}
                          </label>
                          <select
                            value={String(value ?? '')}
                            onChange={(e) => handleConfigChange(field, e.target.value)}
                            className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                          >
                            <option value="">Select...</option>
                            {validValues.map((v) => (
                              <option key={v} value={v}>
                                {v}
                              </option>
                            ))}
                          </select>
                        </div>
                      )
                    }

                    if (typeof value === 'boolean' || field.includes('enable') || field.includes('include') || field === 'online' || field === 'compression' || field === 'copy_only' || field === 'verify_backup') {
                      return (
                        <div key={field} className="flex items-center gap-2">
                          <input
                            type="checkbox"
                            id={field}
                            checked={Boolean(value)}
                            onChange={(e) => handleConfigChange(field, e.target.checked)}
                            className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                          />
                          <label htmlFor={field} className="text-sm text-gray-700">
                            {FIELD_LABELS[field] || field}
                          </label>
                        </div>
                      )
                    }

                    if (field === 'script_content') {
                      return (
                        <div key={field}>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            {FIELD_LABELS[field] || field}
                            {isRequired && <span className="text-red-500"> *</span>}
                          </label>
                          <textarea
                            value={String(value ?? '')}
                            onChange={(e) => handleConfigChange(field, e.target.value)}
                            placeholder="-- Enter your T-SQL script here"
                            className="w-full px-3 py-2 border rounded-lg text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500"
                            rows={6}
                          />
                        </div>
                      )
                    }

                    // Default: text/number input
                    return (
                      <div key={field}>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          {FIELD_LABELS[field] || field}
                          {isRequired && <span className="text-red-500"> *</span>}
                        </label>
                        <Input
                          type={typeof value === 'number' ? 'number' : 'text'}
                          value={String(value ?? '')}
                          onChange={(e) => {
                            const newValue = typeof value === 'number' ? Number(e.target.value) : e.target.value
                            handleConfigChange(field, newValue)
                          }}
                          placeholder={`Enter ${FIELD_LABELS[field]?.toLowerCase() || field}`}
                        />
                      </div>
                    )
                  })}
                </div>
              </div>
            </div>
          )}

          {/* Step 3: Review */}
          {step === 'review' && selectedType && (
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

              <div className="bg-gray-50 rounded-lg p-4 space-y-3">
                <div>
                  <span className="text-sm text-gray-500">Name</span>
                  <p className="font-medium">{name}</p>
                </div>
                <div>
                  <span className="text-sm text-gray-500">Type</span>
                  <p className="font-medium">
                    {POLICY_TYPE_ICONS[selectedType]} {POLICY_TYPE_LABELS[selectedType]}
                  </p>
                </div>
                {description && (
                  <div>
                    <span className="text-sm text-gray-500">Description</span>
                    <p className="font-medium">{description}</p>
                  </div>
                )}
                <div>
                  <span className="text-sm text-gray-500">Configuration</span>
                  <pre className="mt-1 p-2 bg-white rounded border text-sm overflow-x-auto">
                    {JSON.stringify(configuration, null, 2)}
                  </pre>
                </div>
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
            {step === 'details' && (
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
                  Save as Draft
                </Button>
                <Button onClick={() => handleSave(true)} disabled={createMutation.isPending}>
                  {createMutation.isPending && <Spinner size="sm" className="mr-2" />}
                  Save & Activate
                </Button>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

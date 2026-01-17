import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Input } from '../ui/Input'
import { Select } from '../ui/Select'
import { Button } from '../ui/Button'
import { Spinner } from '../ui/Spinner'
import { CheckCircle, XCircle, AlertTriangle } from 'lucide-react'
import { serverService, type TestConnectionResult } from '../../services/serverService'

const serverSchema = z
  .object({
    name: z.string().min(1, 'Display name is required'),
    hostname: z.string().min(1, 'Host is required'),
    port: z.number().min(1, 'Port must be at least 1').max(65535, 'Port must be at most 65535'),
    instanceName: z.string().optional(),
    authType: z.enum(['sql', 'windows']),
    username: z.string().optional(),
    password: z.string().optional(),
  })
  .refine(
    (data) => {
      if (data.authType === 'sql') {
        return data.username && data.username.length > 0
      }
      return true
    },
    { message: 'Username is required for SQL authentication', path: ['username'] }
  )
  .refine(
    (data) => {
      if (data.authType === 'sql') {
        return data.password && data.password.length > 0
      }
      return true
    },
    { message: 'Password is required for SQL authentication', path: ['password'] }
  )

export type ServerFormData = z.infer<typeof serverSchema>

interface ServerFormProps {
  onSubmit: (data: ServerFormData) => Promise<void>
  onCancel: () => void
  isLoading?: boolean
}

export const ServerForm = ({ onSubmit, onCancel, isLoading }: ServerFormProps) => {
  const [testResult, setTestResult] = useState<TestConnectionResult | null>(null)
  const [isTesting, setIsTesting] = useState(false)
  const [connectionTested, setConnectionTested] = useState(false)

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
    getValues,
  } = useForm<ServerFormData>({
    resolver: zodResolver(serverSchema),
    defaultValues: {
      name: '',
      hostname: '',
      port: 1433,
      instanceName: '',
      authType: 'sql',
      username: '',
      password: '',
    },
  })

  const authType = watch('authType')

  const handleTestConnection = async () => {
    const values = getValues()

    // Basic validation before testing
    if (!values.hostname) {
      setTestResult({
        success: false,
        error: 'Host is required',
        error_code: 'VALIDATION_ERROR',
      })
      return
    }

    if (values.authType === 'sql' && !values.username) {
      setTestResult({
        success: false,
        error: 'Username is required for SQL authentication',
        error_code: 'VALIDATION_ERROR',
      })
      return
    }

    setIsTesting(true)
    setTestResult(null)

    const result = await serverService.testConnection({
      hostname: values.hostname,
      port: values.port || 1433,
      instance_name: values.instanceName || undefined,
      auth_type: values.authType,
      username: values.username || undefined,
      password: values.password || undefined,
    })

    setTestResult(result)
    setConnectionTested(result.success)
    setIsTesting(false)
  }

  const handleFormSubmit = async (data: ServerFormData) => {
    await onSubmit(data)
  }

  const canSave = connectionTested && testResult?.success

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4">
      <Input
        label="Display Name"
        placeholder="Production SQL Server"
        error={errors.name?.message}
        {...register('name')}
      />

      <div className="grid grid-cols-2 gap-4">
        <Input
          label="Host"
          placeholder="sql.example.com"
          error={errors.hostname?.message}
          {...register('hostname')}
        />
        <Input
          label="Port"
          type="number"
          placeholder="1433"
          error={errors.port?.message}
          {...register('port', { valueAsNumber: true })}
        />
      </div>

      <Input
        label="Instance Name (optional)"
        placeholder="SQLEXPRESS"
        helperText="Leave blank for default instance"
        error={errors.instanceName?.message}
        {...register('instanceName')}
      />

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Authentication Type</label>
        <Select
          options={[
            { value: 'sql', label: 'SQL Server Authentication' },
            { value: 'windows', label: 'Windows Authentication' },
          ]}
          {...register('authType')}
        />
      </div>

      {authType === 'sql' && (
        <>
          <Input
            label="Username"
            placeholder="sa"
            error={errors.username?.message}
            {...register('username')}
          />
          <Input
            label="Password"
            type="password"
            placeholder="••••••••"
            error={errors.password?.message}
            {...register('password')}
          />
        </>
      )}

      {authType === 'windows' && (
        <p className="text-sm text-gray-500 bg-gray-50 p-3 rounded-md">
          Windows authentication will use the credentials of the DbTools service account.
        </p>
      )}

      {/* Test Connection Section */}
      <div className="border-t border-gray-200 pt-4">
        <div className="flex items-center gap-3">
          <Button
            type="button"
            variant="secondary"
            onClick={handleTestConnection}
            disabled={isTesting}
          >
            {isTesting ? (
              <>
                <Spinner size="sm" />
                <span className="ml-2">Testing...</span>
              </>
            ) : (
              'Test Connection'
            )}
          </Button>

          {testResult && (
            <div className="flex items-center gap-2">
              {testResult.success ? (
                <>
                  <CheckCircle className="h-5 w-5 text-green-500" />
                  <span className="text-sm text-green-700">Connected</span>
                </>
              ) : (
                <>
                  <XCircle className="h-5 w-5 text-red-500" />
                  <span className="text-sm text-red-700">Failed</span>
                </>
              )}
            </div>
          )}
        </div>

        {/* Connection Result Details */}
        {testResult && (
          <div
            className={`mt-3 p-3 rounded-md ${testResult.success ? 'bg-green-50' : 'bg-red-50'}`}
          >
            {testResult.success ? (
              <div className="space-y-1 text-sm">
                <p className="text-green-800">
                  <strong>Edition:</strong> {testResult.edition}
                </p>
                <p className="text-green-800">
                  <strong>Version:</strong> {testResult.product_version}
                </p>
                {!testResult.is_supported_version && (
                  <div className="flex items-center gap-2 text-yellow-700 mt-2">
                    <AlertTriangle className="h-4 w-4" />
                    <span>SQL Server 2016 or later is recommended</span>
                  </div>
                )}
                {!testResult.has_view_server_state && (
                  <div className="flex items-center gap-2 text-yellow-700 mt-2">
                    <AlertTriangle className="h-4 w-4" />
                    <span>VIEW SERVER STATE permission not granted</span>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-sm text-red-800">{testResult.error}</p>
            )}
          </div>
        )}
      </div>

      {/* Form Actions */}
      <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
        <Button type="button" variant="secondary" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" disabled={!canSave || isLoading}>
          {isLoading ? (
            <>
              <Spinner size="sm" />
              <span className="ml-2">Saving...</span>
            </>
          ) : (
            'Save Server'
          )}
        </Button>
      </div>
    </form>
  )
}

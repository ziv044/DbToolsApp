import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import { Modal } from '../ui/Modal'
import { ServerForm, type ServerFormData } from './ServerForm'
import { serverService } from '../../services/serverService'
import { handleApiError } from '../../services/api'
import { toast } from '../ui/toastStore'
import { useTenantStore } from '../../stores/tenantStore'

interface AddServerModalProps {
  isOpen: boolean
  onClose: () => void
}

export const AddServerModal = ({ isOpen, onClose }: AddServerModalProps) => {
  const [isLoading, setIsLoading] = useState(false)
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const currentTenant = useTenantStore((state) => state.currentTenant)

  const handleSubmit = async (data: ServerFormData) => {
    setIsLoading(true)
    try {
      await serverService.create({
        name: data.name,
        hostname: data.hostname,
        port: data.port,
        instance_name: data.instanceName || undefined,
        auth_type: data.authType,
        username: data.username || undefined,
        password: data.password || undefined,
        validate: true,
      })

      toast.success(`Server "${data.name}" added successfully`)

      // Invalidate servers query to refresh the list
      await queryClient.invalidateQueries({ queryKey: ['servers', currentTenant] })

      onClose()
      navigate('/servers')
    } catch (error) {
      toast.error('Failed to add server', handleApiError(error))
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Add Server" size="lg">
      <ServerForm onSubmit={handleSubmit} onCancel={onClose} isLoading={isLoading} />
    </Modal>
  )
}

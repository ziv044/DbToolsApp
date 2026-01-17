import { useState } from 'react'
import { Button, Input, Modal } from '../ui'
import { validateSlug, generateSlug } from '../../services/tenantService'

interface TenantFormProps {
  isOpen: boolean
  onClose: () => void
  onSubmit: (data: { name: string; slug: string }) => void
  isLoading?: boolean
}

export const TenantForm = ({ isOpen, onClose, onSubmit, isLoading = false }: TenantFormProps) => {
  const [name, setName] = useState('')
  const [slug, setSlug] = useState('')
  const [autoGenerateSlug, setAutoGenerateSlug] = useState(true)
  const [errors, setErrors] = useState<{ name?: string; slug?: string }>({})

  const handleNameChange = (value: string) => {
    setName(value)
    if (autoGenerateSlug) {
      setSlug(value ? generateSlug(value) : '')
    }
  }

  const handleSlugChange = (value: string) => {
    setAutoGenerateSlug(false)
    setSlug(value.toLowerCase().replace(/[^a-z0-9-]/g, ''))
  }

  const handleClose = () => {
    setName('')
    setSlug('')
    setAutoGenerateSlug(true)
    setErrors({})
    onClose()
  }

  const validate = (): boolean => {
    const newErrors: { name?: string; slug?: string } = {}

    if (!name.trim()) {
      newErrors.name = 'Name is required'
    }

    if (!slug.trim()) {
      newErrors.slug = 'Slug is required'
    } else if (!validateSlug(slug)) {
      newErrors.slug =
        'Slug must be 3-50 characters, lowercase alphanumeric with hyphens, not starting/ending with hyphen'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (validate()) {
      onSubmit({ name: name.trim(), slug })
    }
  }

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Create New Tenant" size="md">
      <form onSubmit={handleSubmit}>
        <div className="space-y-4">
          <Input
            label="Tenant Name"
            name="name"
            value={name}
            onChange={(e) => handleNameChange(e.target.value)}
            placeholder="Enter tenant name"
            error={errors.name}
            disabled={isLoading}
          />

          <div>
            <Input
              label="Slug"
              name="slug"
              value={slug}
              onChange={(e) => handleSlugChange(e.target.value)}
              placeholder="tenant-slug"
              error={errors.slug}
              helperText="Used in URLs and database names. Auto-generated from name."
              disabled={isLoading}
            />
            {!autoGenerateSlug && (
              <button
                type="button"
                onClick={() => {
                  setAutoGenerateSlug(true)
                  setSlug(generateSlug(name))
                }}
                className="mt-1 text-sm text-blue-600 hover:text-blue-700"
              >
                Auto-generate from name
              </button>
            )}
          </div>
        </div>

        <div className="flex justify-end gap-3 mt-6">
          <Button type="button" variant="secondary" onClick={handleClose} disabled={isLoading}>
            Cancel
          </Button>
          <Button type="submit" disabled={isLoading}>
            {isLoading ? 'Creating...' : 'Create Tenant'}
          </Button>
        </div>
      </form>
    </Modal>
  )
}

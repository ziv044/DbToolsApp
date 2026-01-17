import { useState } from 'react'
import { MoreVertical, Pause, Play, Trash2 } from 'lucide-react'
import { Table, TableHeader, TableBody, TableRow, TableCell, Badge, ConfirmDialog } from '../ui'
import type { Tenant } from '../../services/tenantService'

interface TenantListProps {
  tenants: Tenant[]
  onSuspend: (slug: string) => void
  onActivate: (slug: string) => void
  onDelete: (slug: string) => void
  isUpdating?: string | null
}

export const TenantList = ({
  tenants,
  onSuspend,
  onActivate,
  onDelete,
  isUpdating,
}: TenantListProps) => {
  const [deleteConfirm, setDeleteConfirm] = useState<Tenant | null>(null)
  const [openMenuId, setOpenMenuId] = useState<string | null>(null)

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }

  const handleMenuClick = (id: string) => {
    setOpenMenuId(openMenuId === id ? null : id)
  }

  const handleAction = (action: () => void) => {
    action()
    setOpenMenuId(null)
  }

  return (
    <>
      <Table>
        <TableHeader>
          <TableRow>
            <TableCell header>Name</TableCell>
            <TableCell header>Slug</TableCell>
            <TableCell header>Status</TableCell>
            <TableCell header>Created</TableCell>
            <TableCell header>Actions</TableCell>
          </TableRow>
        </TableHeader>
        <TableBody>
          {tenants.length === 0 ? (
            <TableRow>
              <TableCell className="text-center text-gray-500 py-8" colSpan={5}>
                No tenants found. Create your first tenant to get started.
              </TableCell>
            </TableRow>
          ) : (
            tenants.map((tenant) => (
              <TableRow key={tenant.id}>
                <TableCell className="font-medium">{tenant.name}</TableCell>
                <TableCell>
                  <code className="text-sm bg-gray-100 px-2 py-1 rounded">{tenant.slug}</code>
                </TableCell>
                <TableCell>
                  <Badge variant={tenant.status === 'active' ? 'success' : 'warning'}>
                    {tenant.status}
                  </Badge>
                </TableCell>
                <TableCell>{formatDate(tenant.created_at)}</TableCell>
                <TableCell>
                  <div className="relative">
                    <button
                      onClick={() => handleMenuClick(tenant.id)}
                      className="p-1 hover:bg-gray-100 rounded transition-colors"
                      disabled={isUpdating === tenant.slug}
                    >
                      <MoreVertical className="h-5 w-5 text-gray-500" />
                    </button>

                    {openMenuId === tenant.id && (
                      <>
                        <div className="fixed inset-0 z-10" onClick={() => setOpenMenuId(null)} />
                        <div className="absolute right-0 top-full mt-1 z-20 bg-white border border-gray-200 rounded-md shadow-lg py-1 min-w-[140px]">
                          {tenant.status === 'active' ? (
                            <button
                              onClick={() => handleAction(() => onSuspend(tenant.slug))}
                              className="flex items-center gap-2 w-full px-4 py-2 text-sm text-left hover:bg-gray-50 text-yellow-600"
                            >
                              <Pause className="h-4 w-4" />
                              Suspend
                            </button>
                          ) : (
                            <button
                              onClick={() => handleAction(() => onActivate(tenant.slug))}
                              className="flex items-center gap-2 w-full px-4 py-2 text-sm text-left hover:bg-gray-50 text-green-600"
                            >
                              <Play className="h-4 w-4" />
                              Activate
                            </button>
                          )}
                          <button
                            onClick={() => {
                              setDeleteConfirm(tenant)
                              setOpenMenuId(null)
                            }}
                            className="flex items-center gap-2 w-full px-4 py-2 text-sm text-left hover:bg-gray-50 text-red-600"
                          >
                            <Trash2 className="h-4 w-4" />
                            Delete
                          </button>
                        </div>
                      </>
                    )}
                  </div>
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>

      <ConfirmDialog
        isOpen={!!deleteConfirm}
        onClose={() => setDeleteConfirm(null)}
        onConfirm={() => {
          if (deleteConfirm) {
            onDelete(deleteConfirm.slug)
            setDeleteConfirm(null)
          }
        }}
        title="Delete Tenant"
        description={`Are you sure you want to delete "${deleteConfirm?.name}"? This action cannot be undone and all tenant data will be permanently removed.`}
        confirmLabel="Delete"
        variant="danger"
        isLoading={isUpdating === deleteConfirm?.slug}
      />
    </>
  )
}

import { useEffect, useState } from 'react'
import { X, CheckCircle, XCircle, AlertCircle } from 'lucide-react'
import { toast } from './toastStore'
import type { ToastItem } from './toastStore'

export interface ToastProps {
  id: string
  title: string
  description?: string
  variant?: 'default' | 'success' | 'error' | 'warning'
  duration?: number
  onClose: (id: string) => void
}

const variantStyles = {
  default: 'bg-white border-gray-200',
  success: 'bg-green-50 border-green-200',
  error: 'bg-red-50 border-red-200',
  warning: 'bg-yellow-50 border-yellow-200',
}

const variantIcons = {
  default: null,
  success: CheckCircle,
  error: XCircle,
  warning: AlertCircle,
}

const variantIconColors = {
  default: '',
  success: 'text-green-500',
  error: 'text-red-500',
  warning: 'text-yellow-500',
}

export const Toast = ({
  id,
  title,
  description,
  variant = 'default',
  duration = 5000,
  onClose,
}: ToastProps) => {
  useEffect(() => {
    const timer = setTimeout(() => {
      onClose(id)
    }, duration)
    return () => clearTimeout(timer)
  }, [id, duration, onClose])

  const Icon = variantIcons[variant]

  return (
    <div
      className={`flex items-start gap-3 p-4 rounded-lg border shadow-lg ${variantStyles[variant]} animate-slide-in`}
    >
      {Icon && <Icon className={`h-5 w-5 mt-0.5 ${variantIconColors[variant]}`} />}
      <div className="flex-1">
        <p className="font-medium text-gray-900">{title}</p>
        {description && <p className="text-sm text-gray-600 mt-1">{description}</p>}
      </div>
      <button
        onClick={() => onClose(id)}
        className="text-gray-400 hover:text-gray-600 transition-colors"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  )
}

export const ToastContainer = () => {
  const [toasts, setToasts] = useState<ToastItem[]>([])

  useEffect(() => {
    return toast.subscribe(setToasts)
  }, [])

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-md">
      {toasts.map((t) => (
        <Toast key={t.id} {...t} onClose={toast.dismiss} />
      ))}
    </div>
  )
}

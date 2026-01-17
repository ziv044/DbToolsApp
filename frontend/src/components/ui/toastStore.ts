interface ToastItem {
  id: string
  title: string
  description?: string
  variant?: 'default' | 'success' | 'error' | 'warning'
  duration?: number
}

let toastListeners: ((toasts: ToastItem[]) => void)[] = []
let toastQueue: ToastItem[] = []

export const toast = {
  show: (options: Omit<ToastItem, 'id'>) => {
    const id = Math.random().toString(36).slice(2)
    const newToast = { ...options, id }
    toastQueue = [...toastQueue, newToast]
    toastListeners.forEach((listener) => listener(toastQueue))
    return id
  },
  success: (title: string, description?: string) => {
    return toast.show({ title, description, variant: 'success' })
  },
  error: (title: string, description?: string) => {
    return toast.show({ title, description, variant: 'error' })
  },
  warning: (title: string, description?: string) => {
    return toast.show({ title, description, variant: 'warning' })
  },
  dismiss: (id: string) => {
    toastQueue = toastQueue.filter((t) => t.id !== id)
    toastListeners.forEach((listener) => listener(toastQueue))
  },
  subscribe: (listener: (toasts: ToastItem[]) => void) => {
    toastListeners.push(listener)
    return () => {
      toastListeners = toastListeners.filter((l) => l !== listener)
    }
  },
  getQueue: () => [...toastQueue],
}

export type { ToastItem }

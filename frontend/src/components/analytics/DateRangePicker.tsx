import { useState } from 'react'
import { Calendar, ChevronDown } from 'lucide-react'
import { Button } from '../ui'
import type { DateRange } from '../../services/analyticsService'

interface DateRangePickerProps {
  value: DateRange
  onChange: (range: DateRange) => void
}

const PRESETS = [
  { label: 'Last 1 hour', hours: 1 },
  { label: 'Last 6 hours', hours: 6 },
  { label: 'Last 24 hours', hours: 24 },
  { label: 'Last 7 days', hours: 24 * 7 },
  { label: 'Last 30 days', hours: 24 * 30 },
]

const formatRange = (range: DateRange): string => {
  const formatDate = (d: Date) => {
    return d.toLocaleDateString([], { month: 'short', day: 'numeric' }) +
      ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }
  return `${formatDate(range.start)} - ${formatDate(range.end)}`
}

export const DateRangePicker = ({ value, onChange }: DateRangePickerProps) => {
  const [isOpen, setIsOpen] = useState(false)

  const handlePreset = (hours: number) => {
    const end = new Date()
    const start = new Date(end.getTime() - hours * 60 * 60 * 1000)
    onChange({ start, end })
    setIsOpen(false)
  }

  return (
    <div className="relative">
      <Button
        variant="secondary"
        onClick={() => setIsOpen(!isOpen)}
        className="w-72 justify-start text-left font-normal"
      >
        <Calendar className="mr-2 h-4 w-4" />
        <span className="flex-1 truncate text-sm">{formatRange(value)}</span>
        <ChevronDown className="ml-2 h-4 w-4 opacity-50" />
      </Button>

      {isOpen && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setIsOpen(false)} />
          <div className="absolute right-0 top-full mt-1 z-20 bg-white rounded-lg shadow-lg border border-gray-200 p-2 min-w-48">
            {PRESETS.map(preset => (
              <button
                key={preset.hours}
                className="w-full text-left px-3 py-2 text-sm rounded hover:bg-gray-100 transition-colors"
                onClick={() => handlePreset(preset.hours)}
              >
                {preset.label}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  )
}

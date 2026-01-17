import { X } from 'lucide-react';

interface LabelBadgeProps {
  name: string;
  color?: string;
  onRemove?: () => void;
  size?: 'sm' | 'md';
}

function getContrastColor(hexColor: string): string {
  // Remove # if present
  const hex = hexColor.replace('#', '');

  // Convert to RGB
  const r = parseInt(hex.substring(0, 2), 16);
  const g = parseInt(hex.substring(2, 4), 16);
  const b = parseInt(hex.substring(4, 6), 16);

  // Calculate luminance
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;

  // Return white for dark colors, dark gray for light colors
  return luminance > 0.5 ? '#1f2937' : '#ffffff';
}

export function LabelBadge({ name, color = '#6B7280', onRemove, size = 'sm' }: LabelBadgeProps) {
  const textColor = getContrastColor(color);
  const sizeClasses = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-sm';

  return (
    <span
      className={`inline-flex items-center rounded font-medium ${sizeClasses}`}
      style={{ backgroundColor: color, color: textColor }}
    >
      {name}
      {onRemove && (
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onRemove();
          }}
          className="ml-1 hover:opacity-75 focus:outline-none"
        >
          <X className={size === 'sm' ? 'h-3 w-3' : 'h-4 w-4'} />
        </button>
      )}
    </span>
  );
}

export default LabelBadge;

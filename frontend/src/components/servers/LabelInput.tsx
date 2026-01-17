import { useState, useRef, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { labelService } from '../../services/labelService';
import { LabelBadge } from '../common/LabelBadge';
import { toast } from '../ui/toastStore';

// Simple label type that only requires id, name, and color
interface SimpleLabel {
  id: string;
  name: string;
  color: string;
}

interface LabelInputProps {
  serverId: string;
  existingLabels: SimpleLabel[];
  onLabelsChange?: (labels: SimpleLabel[]) => void;
}

export function LabelInput({ serverId, existingLabels, onLabelsChange }: LabelInputProps) {
  const queryClient = useQueryClient();
  const [inputValue, setInputValue] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Fetch all labels for autocomplete
  const { data: allLabelsData } = useQuery({
    queryKey: ['labels'],
    queryFn: labelService.getAll,
  });

  const allLabels = allLabelsData?.labels || [];

  // Filter labels for autocomplete suggestions
  const suggestions = allLabels.filter(
    (label) =>
      label.name.toLowerCase().includes(inputValue.toLowerCase()) &&
      !existingLabels.some((existing) => existing.id === label.id)
  );

  // Add label mutation
  const addLabelMutation = useMutation({
    mutationFn: (labelNames: string[]) => labelService.assignToServer(serverId, labelNames),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['servers', serverId] });
      queryClient.invalidateQueries({ queryKey: ['labels'] });
      if (onLabelsChange) {
        onLabelsChange(data.labels);
      }
      setInputValue('');
      toast.success('Label added');
    },
    onError: () => {
      toast.error('Failed to add label');
    },
  });

  // Remove label mutation
  const removeLabelMutation = useMutation({
    mutationFn: (labelId: string) => labelService.removeFromServer(serverId, labelId),
    onSuccess: (_, labelId) => {
      queryClient.invalidateQueries({ queryKey: ['servers', serverId] });
      queryClient.invalidateQueries({ queryKey: ['labels'] });
      if (onLabelsChange) {
        onLabelsChange(existingLabels.filter((l) => l.id !== labelId));
      }
      toast.success('Label removed');
    },
    onError: () => {
      toast.error('Failed to remove label');
    },
  });

  // Handle click outside to close dropdown
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node) &&
        !inputRef.current?.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleAddLabel = (labelName: string) => {
    if (labelName.trim()) {
      addLabelMutation.mutate([labelName.trim()]);
    }
    setIsOpen(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && inputValue.trim()) {
      e.preventDefault();
      handleAddLabel(inputValue);
    } else if (e.key === 'Escape') {
      setIsOpen(false);
    }
  };

  return (
    <div className="space-y-2">
      {/* Existing labels */}
      {existingLabels.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {existingLabels.map((label) => (
            <LabelBadge
              key={label.id}
              name={label.name}
              color={label.color}
              onRemove={() => removeLabelMutation.mutate(label.id)}
            />
          ))}
        </div>
      )}

      {/* Input with autocomplete */}
      <div className="relative">
        <input
          ref={inputRef}
          type="text"
          value={inputValue}
          onChange={(e) => {
            setInputValue(e.target.value);
            setIsOpen(true);
          }}
          onFocus={() => setIsOpen(true)}
          onKeyDown={handleKeyDown}
          placeholder="Add label..."
          className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />

        {/* Dropdown */}
        {isOpen && inputValue && (
          <div
            ref={dropdownRef}
            className="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded-md shadow-lg max-h-48 overflow-auto"
          >
            {suggestions.length > 0 ? (
              suggestions.slice(0, 10).map((label) => (
                <button
                  key={label.id}
                  type="button"
                  onClick={() => handleAddLabel(label.name)}
                  className="w-full px-3 py-2 text-left text-sm hover:bg-gray-100 flex items-center gap-2"
                >
                  <span
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: label.color }}
                  />
                  {label.name}
                </button>
              ))
            ) : (
              <button
                type="button"
                onClick={() => handleAddLabel(inputValue)}
                className="w-full px-3 py-2 text-left text-sm hover:bg-gray-100"
              >
                Create &ldquo;{inputValue}&rdquo;
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default LabelInput;

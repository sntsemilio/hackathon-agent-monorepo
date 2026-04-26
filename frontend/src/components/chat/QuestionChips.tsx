import { ScrollArea, ScrollBar } from '../ui/scroll-area';

interface QuestionChipsProps {
  questions: string[];
  onSelect: (q: string) => void;
  disabled?: boolean;
}

export function QuestionChips({ questions, onSelect, disabled }: QuestionChipsProps) {
  if (!questions || questions.length === 0) return null;

  return (
    <ScrollArea className="w-full whitespace-nowrap pb-2">
      <div className="flex w-max space-x-2">
        {questions.map((q, i) => (
          <button
            key={i}
            onClick={() => onSelect(q)}
            disabled={disabled}
            className="inline-flex items-center rounded-full bg-white shadow-sm px-4 py-2 text-xs font-semibold text-gray-700 transition-colors hover:bg-gray-50 hover:text-[var(--hey-primary)] hover:shadow-md disabled:opacity-50 disabled:cursor-not-allowed border border-transparent"
          >
            {q}
          </button>
        ))}
      </div>
      <ScrollBar orientation="horizontal" className="hidden" />
    </ScrollArea>
  );
}

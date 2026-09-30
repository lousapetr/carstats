import { Button } from './Button'

export function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div
      role="alert"
      className="flex flex-col items-start gap-2 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-300"
    >
      <p>{message}</p>
      <Button type="button" variant="secondary" onClick={onRetry}>
        Zkusit znovu
      </Button>
    </div>
  )
}

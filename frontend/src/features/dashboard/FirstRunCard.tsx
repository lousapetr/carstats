import { Link } from 'react-router-dom'
import { Card } from '../../components/ui/Card'

const linkClass =
  'rounded-lg bg-gray-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-gray-700 dark:bg-gray-200 dark:text-gray-900 dark:hover:bg-gray-300'

/** Shown instead of a grid of zeroes until the first entry is logged. */
export function FirstRunCard() {
  return (
    <Card className="flex flex-col gap-3">
      <h2 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
        Zatím tu nic není
      </h2>
      <p className="text-sm text-gray-600 dark:text-gray-400">
        Přehled nákladů a spotřeby se začne plnit, jakmile zapíšete první tankování nebo servis.
      </p>
      <div className="flex flex-wrap gap-2">
        <Link to="/fuel" className={linkClass}>
          Zapsat tankování
        </Link>
        <Link to="/maintenance" className={linkClass}>
          Zapsat servis
        </Link>
      </div>
    </Card>
  )
}

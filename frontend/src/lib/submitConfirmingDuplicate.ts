import { isDuplicateConflict } from '../api/errors'
import { confirmDialog } from './confirmBus'

/** Submits; on a duplicate 409 asks the user, then resubmits with force.
 *  A cancel rethrows so the form keeps its input. */
export async function submitConfirmingDuplicate<T>(
  submit: (force: boolean) => Promise<T>,
): Promise<T> {
  try {
    return await submit(false)
  } catch (error) {
    if (!isDuplicateConflict(error)) throw error
    const confirmed = await confirmDialog(
      `${error.detail ?? 'Takový záznam už existuje.'} Přesto uložit?`,
      { confirmLabel: 'Přesto uložit', variant: 'primary' },
    )
    if (!confirmed) throw error
    return submit(true)
  }
}

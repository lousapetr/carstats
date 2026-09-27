import { useEffect, useState } from 'react'

const QUERY = '(prefers-color-scheme: dark)'

/** Tracks the OS colour scheme — the same signal Tailwind's `dark:` variant
 *  uses — so chart colours passed as props follow a live theme switch instead
 *  of freezing at first render.
 */
export function useIsDark(): boolean {
  const [isDark, setIsDark] = useState(
    () => typeof window !== 'undefined' && window.matchMedia(QUERY).matches,
  )

  useEffect(() => {
    const media = window.matchMedia(QUERY)
    const onChange = (event: MediaQueryListEvent) => setIsDark(event.matches)
    media.addEventListener('change', onChange)
    return () => media.removeEventListener('change', onChange)
  }, [])

  return isDark
}

import type { ReactNode } from 'react'

/** Gives a chart's SVG an accessible name: screen readers announce the
 *  caption, while recharts' own accessibility layer handles keyboard focus.
 */
export function ChartFigure({ caption, children }: { caption: string; children: ReactNode }) {
  return (
    <figure>
      <figcaption className="sr-only">{caption}</figcaption>
      {children}
    </figure>
  )
}

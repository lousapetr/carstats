import type { UseQueryResult } from '@tanstack/react-query'
import { useEffect, useRef } from 'react'
import { useSearchParams } from 'react-router-dom'

/**
 * Opens the entry named by `?edit=<id>` (linked from the dashboard), then drops the parameter.
 * An id missing from cached data is only given up on after a fetch made since mount, so a
 * draft created after the list was last loaded is still found.
 */
export function useEditParam<T extends { id: number }>(
  query: UseQueryResult<T[]>,
  onOpen: (entry: T) => void,
) {
  const [searchParams, setSearchParams] = useSearchParams()
  const editId = searchParams.get('edit')
  const onOpenRef = useRef(onOpen)
  onOpenRef.current = onOpen
  const { data, isFetching, isFetchedAfterMount, refetch } = query

  useEffect(() => {
    if (editId === null || !data) return
    const entry = data.find((e) => e.id === Number(editId))
    if (!entry) {
      if (isFetching) return
      if (!isFetchedAfterMount) {
        void refetch()
        return
      }
    } else {
      onOpenRef.current(entry)
    }
    setSearchParams(
      (params) => {
        params.delete('edit')
        return params
      },
      { replace: true },
    )
  }, [editId, data, isFetching, isFetchedAfterMount, refetch, setSearchParams])
}

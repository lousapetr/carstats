import '@tanstack/react-query'

declare module '@tanstack/react-query' {
  interface Register {
    mutationMeta: {
      /** Toasted by the global MutationCache on success. */
      successMessage?: string
      /** A 409 from this mutation is handled by submitConfirmingDuplicate, not toasted. */
      confirmsDuplicate?: boolean
    }
  }
}

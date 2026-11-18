import '@tanstack/react-query'

declare module '@tanstack/react-query' {
  interface Register {
    mutationMeta: {
      /** Toasted by the global MutationCache on success; a function picks the text from the response. */
      successMessage?: string | ((data: unknown) => string)
      /** A 409 from this mutation is handled by submitConfirmingDuplicate, not toasted. */
      confirmsDuplicate?: boolean
    }
  }
}

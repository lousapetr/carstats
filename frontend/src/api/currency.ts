import { api } from './client'
import type { CurrencyRate } from '../types'

export const currencyApi = {
  list: () => api.get<CurrencyRate[]>('/api/currency-rates'),
}

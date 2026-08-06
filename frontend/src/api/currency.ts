import { api } from './client'
import type { Currency, CurrencyRate } from '../types'

export const currencyApi = {
  list: () => api.get<CurrencyRate[]>('/api/currency-rates'),
  update: (currency: Currency, rate_to_czk: number) =>
    api.put<CurrencyRate>(`/api/currency-rates/${currency}`, { rate_to_czk }),
}

/** Normaliza a digitação de valores ("18,50" → "18.50"). Não faz cálculos: o servidor valida e calcula. */
export function normalizeMoneyInput(value: string): string {
  return value.trim().replace(/\s/g, '').replace(/\.(?=\d{3}(\D|$))/g, '').replace(',', '.')
}

export const MONEY_PATTERN = /^\d{1,7}([.,]\d{1,2})?$/

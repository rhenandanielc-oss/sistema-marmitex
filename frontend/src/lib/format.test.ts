import { describe, expect, it } from 'vitest'

import { formatCnpj, formatDate, formatDayMonth, formatInt, formatMoney, formatPercent, isNegative, todayIso } from './format'
import { normalizeMoneyInput, MONEY_PATTERN } from './money'

const nbsp = (s: string) => s.replace(/ /g, ' ')

describe('formatação pt-BR (FE-05)', () => {
  it('formata dinheiro vindo da API como string', () => {
    expect(nbsp(formatMoney('1234.5'))).toBe('R$ 1.234,50')
    expect(nbsp(formatMoney('801.67'))).toBe('R$ 801,67')
    expect(nbsp(formatMoney('-300.00'))).toBe('-R$ 300,00')
    expect(formatMoney(null)).toBe('—')
  })
  it('formata datas sem conversão de fuso', () => {
    expect(formatDate('2026-09-01')).toBe('01/09/2026')
    expect(formatDate('2026-09-30T23:59:00Z')).toBe('30/09/2026')
    expect(formatDayMonth('2026-09-01')).toBe('01/09')
    expect(formatDate(null)).toBe('—')
  })
  it('formata inteiros, percentuais e CNPJ', () => {
    expect(formatInt(4739)).toBe('4.739')
    expect(formatPercent('52.23')).toBe('52,23%')
    expect(formatPercent(null)).toBe('—')
    expect(formatCnpj('11222333000181')).toBe('11.222.333/0001-81')
  })
  it('identifica valores negativos e data local', () => {
    expect(isNegative('-1.00')).toBe(true)
    expect(isNegative('0.00')).toBe(false)
    expect(todayIso(new Date(2026, 8, 5))).toBe('2026-09-05')
  })
})

describe('digitação de valores', () => {
  it('normaliza vírgula decimal sem calcular nada', () => {
    expect(normalizeMoneyInput('18,50')).toBe('18.50')
    expect(normalizeMoneyInput(' 18.50 ')).toBe('18.50')
    expect(normalizeMoneyInput('1500')).toBe('1500')
  })
  it('aceita no máximo 2 casas decimais', () => {
    expect(MONEY_PATTERN.test('18,50')).toBe(true)
    expect(MONEY_PATTERN.test('18,505')).toBe(false)
    expect(MONEY_PATTERN.test('abc')).toBe(false)
  })
})

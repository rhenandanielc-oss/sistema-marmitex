import { expect, test, type Page } from '@playwright/test'

/** Fluxos principais (TEST-PLAN.md seção 9). Nomes únicos para poder repetir a execução. */
const EMAIL = process.env.E2E_EMAIL ?? 'dono@marmitaria-exemplo.com.br'
const PASSWORD = process.env.E2E_PASSWORD ?? 'senha-local-123'
const RUN = Date.now().toString(36)

const nbsp = (s: string | null) => (s ?? '').replace(/\u00a0/g, ' ')

function isoDaysAgo(days: number): string {
  const d = new Date()
  d.setDate(d.getDate() - days)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

async function login(page: Page) {
  await page.goto('/login')
  await page.getByLabel('E-mail').fill(EMAIL)
  await page.getByLabel('Senha').fill(PASSWORD)
  await page.getByRole('button', { name: 'Entrar' }).click()
  await expect(page).toHaveURL(/\/dashboard/)
}

async function apiGet(page: Page, path: string) {
  const token = await page.evaluate(() => sessionStorage.getItem('marmitex.token'))
  const res = await page.request.get(`/api/v1${path}`, { headers: { Authorization: `Bearer ${token}` } })
  expect(res.ok()).toBeTruthy()
  return res.json()
}

async function selectOptionByText(page: Page, selector: string, text: string) {
  const select = page.locator(selector)
  await expect(select.locator('option', { hasText: text }).first()).toBeAttached()
  const value = await select.locator('option', { hasText: text }).first().getAttribute('value')
  await select.selectOption(value!)
}

test('cadastro, vendas para empresa e cliente, histórico e dashboard', async ({ page }) => {
  const company = `Construtora E2E ${RUN}`
  const customer = `Cliente E2E ${RUN}`
  await login(page)

  await page.getByRole('link', { name: 'Empresas' }).click()
  await page.getByRole('button', { name: 'Nova empresa' }).click()
  const dialog = page.getByRole('dialog')
  await dialog.locator('#name').fill(company)
  await dialog.locator('#location').fill('Obra Teste E2E')
  await dialog.locator('#billing_cycle').selectOption('QUINZENAL')
  await dialog.locator('#start_date').fill('2026-09-01')
  await dialog.locator('#payment_date').fill('2026-10-15')
  await page.getByRole('button', { name: 'Salvar' }).click()
  await expect(page.getByRole('status').last()).toContainText('Empresa cadastrada')

  await page.getByRole('link', { name: 'Clientes avulsos' }).click()
  await page.getByRole('button', { name: 'Novo cliente' }).click()
  await page.getByRole('dialog').locator('#name').fill(customer)
  await page.getByRole('button', { name: 'Salvar' }).click()
  await expect(page.getByRole('status').last()).toContainText('Cliente cadastrado')

  await page.getByRole('link', { name: 'Vendas' }).click()
  await selectOptionByText(page, '#new-buyer', company)
  await page.getByLabel(/Preço unitário/).fill('18,50')
  await page.getByLabel(/Quantidade/).fill('40')
  await page.getByRole('button', { name: 'Registrar venda' }).click()
  await expect(page.getByRole('status').last()).toContainText('740,00')

  await page.getByLabel('Cliente avulso').check()
  await selectOptionByText(page, '#new-buyer', customer)
  await page.getByLabel(/Preço unitário/).fill('22,00')
  await page.getByLabel(/Quantidade/).fill('5')
  await page.getByRole('button', { name: 'Registrar venda' }).click()
  await expect(page.getByRole('status').last()).toContainText('110,00')
  await expect(page.getByRole('cell', { name: new RegExp(company) })).toBeVisible()

  // Venda pendente → marcar como paga.
  const saleRow = page.getByRole('row', { name: new RegExp(company) }).first()
  await expect(saleRow).toContainText('Pendente')
  await expect(saleRow).toContainText('Obra')
  await saleRow.getByRole('button', { name: 'Marcar pago' }).click()
  await expect(page.getByRole('status').last()).toContainText('marcada como paga')
  await expect(page.getByRole('row', { name: new RegExp(company) }).first()).toContainText('Pago')

  // Histórico filtrado pela empresa = valor para cobrança.
  const companyId = (await apiGet(page, `/companies?q=${encodeURIComponent(company)}`)).items[0].id
  await page.goto(`/historico?empresa=${companyId}`)
  await expect(page.getByText('Total de vendas').locator('..')).toContainText('740,00')

  // Dashboard mostra exatamente o que a API calculou.
  await page.goto('/dashboard?periodo=today')
  const summary = await apiGet(page, '/dashboard/summary?period=today')
  const brl = (v: string) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(Number(v))
  const revenueCard = page.getByText('Receita total').locator('..')
  await expect.poll(async () => nbsp(await revenueCard.textContent())).toContain(nbsp(brl(summary.revenue)))
  const profitCard = page.getByText('Lucro líquido').first().locator('..')
  await expect.poll(async () => nbsp(await profitCard.textContent())).toContain(nbsp(brl(summary.net_profit)))

  // Dashboard da empresa: somente faturamento.
  await page.goto(`/dashboard?periodo=today&empresa=${companyId}`)
  await expect(page.getByRole('heading', { name: company })).toBeVisible()
  await expect(page.getByText('Faturamento', { exact: true }).locator('..')).toContainText('740,00')
  await expect(page.getByText('Data de pagamento:')).toBeVisible()
})

test('novo tipo de custo, custos somando no acumulado', async ({ page }) => {
  const category = `Descartáveis ${RUN}`
  await login(page)
  await page.getByRole('link', { name: 'Tipos de custo' }).click()
  await page.getByRole('button', { name: 'Novo tipo de custo' }).click()
  await page.getByRole('dialog').locator('#name').fill(category)
  await page.getByRole('dialog').locator('#cost_type').selectOption('CUSTO_DIARIO')
  await page.getByRole('button', { name: 'Salvar' }).click()
  await expect(page.getByRole('status').last()).toContainText('Tipo de custo cadastrado')

  await page.getByRole('link', { name: 'Custos' }).click()
  const totalCard = page.getByText('Custos totais no mês').locator('..')
  await expect(totalCard).not.toContainText('—')
  const before = (await apiGet(page, '/costs/summary')).total_costs as string

  await selectOptionByText(page, '#new-category', category)
  await page.getByLabel(/Valor/).fill('45,90')
  await page.getByRole('button', { name: 'Registrar custo' }).click()
  await expect(page.getByRole('status').last()).toContainText('45,90')

  const after = (await apiGet(page, '/costs/summary')).total_costs as string
  expect(Number(after) - Number(before)).toBeCloseTo(45.9, 2)
  const row = page.getByRole('row', { name: new RegExp(category) }).first()
  await expect(row).toContainText('45,90')
  const listing = await apiGet(page, '/costs?sort=cost_date&order=desc&page_size=1&start_date=' + isoDaysAgo(0).slice(0, 8) + '01')
  await expect(row).toContainText(nbsp(new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 2 }).format(Number(listing.items[0].running_total))))
})

test('venda esquecida com data de ontem e empresa desativada fora do lançamento', async ({ page }) => {
  const company = `Empreiteira Antiga ${RUN}`
  await login(page)
  await page.getByRole('link', { name: 'Empresas' }).click()
  await page.getByRole('button', { name: 'Nova empresa' }).click()
  await page.getByRole('dialog').locator('#name').fill(company)
  await page.getByRole('button', { name: 'Salvar' }).click()
  await expect(page.getByRole('status').last()).toContainText('Empresa cadastrada')

  const yesterday = isoDaysAgo(1)
  await page.getByRole('link', { name: 'Vendas' }).click()
  await selectOptionByText(page, '#new-buyer', company)
  await page.getByLabel(/Preço unitário/).fill('10,00')
  await page.getByLabel(/Quantidade/).fill('3')
  await page.locator('#new-date').fill(yesterday)
  await page.getByRole('button', { name: 'Registrar venda' }).click()
  await expect(page.getByRole('status').last()).toContainText('30,00')
  const companyId = (await apiGet(page, `/companies?q=${encodeURIComponent(company)}`)).items[0].id
  const sales = await apiGet(page, `/sales?company_id=${companyId}`)
  expect(sales.items[0].sale_date).toBe(yesterday)

  await page.getByRole('link', { name: 'Empresas' }).click()
  await page.getByPlaceholder(/Pesquisar/).fill(company)
  await page.getByRole('row', { name: new RegExp(company) }).getByRole('button', { name: 'Desativar' }).click()
  await expect(page.getByRole('status').last()).toContainText('desativado')

  await page.getByRole('link', { name: 'Vendas' }).click()
  const select = page.locator('#new-buyer')
  await expect(select.locator('option', { hasText: 'Construtora' }).first()).toBeAttached()
  await expect(select.locator('option', { hasText: company })).toHaveCount(0)

  await page.goto(`/historico?empresa=${companyId}&inicio=${yesterday}&fim=${yesterday}`)
  await expect(page.getByText('Total de vendas').locator('..')).toContainText('30,00')
})

test('logout invalida a sessão', async ({ page }) => {
  await login(page)
  await page.getByRole('button', { name: 'Sair' }).click()
  await expect(page).toHaveURL(/\/login/)
  await page.goto('/dashboard')
  await expect(page.getByRole('button', { name: 'Entrar' })).toBeVisible()
})

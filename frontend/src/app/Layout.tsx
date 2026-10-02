import { NavLink, Outlet } from 'react-router-dom'

import { useAuth } from '../auth/AuthContext'
import { Button, cx } from '../components/ui'

const SECTIONS: { title: string; links: { to: string; label: string }[] }[] = [
  { title: 'Visão geral', links: [{ to: '/dashboard', label: 'Dashboard' }] },
  {
    title: 'Lançamentos',
    links: [
      { to: '/lancamentos/vendas', label: 'Vendas' },
      { to: '/lancamentos/custos', label: 'Custos' },
    ],
  },
  { title: 'Banco de dados', links: [{ to: '/historico', label: 'Histórico' }] },
  {
    title: 'Cadastros',
    links: [
      { to: '/cadastros/empresas', label: 'Empresas' },
      { to: '/cadastros/clientes', label: 'Clientes avulsos' },
      { to: '/cadastros/categorias', label: 'Tipos de custo' },
    ],
  },
  { title: 'Administração', links: [{ to: '/usuarios', label: 'Usuários' }] },
]

export function Layout() {
  const { user, logout } = useAuth()
  return (
    <div className="flex min-h-screen">
      <aside className="w-56 shrink-0 border-r border-slate-200 bg-white">
        <div className="border-b border-slate-100 px-4 py-4">
          <div className="text-base font-bold text-brand-700">Marmitex B2B</div>
          <div className="text-xs text-slate-500">Vendas e financeiro</div>
        </div>
        <nav className="flex flex-col gap-4 px-2 py-4" aria-label="Menu principal">
          {SECTIONS.map((section) => (
            <div key={section.title}>
              <div className="px-2 pb-1 text-xs font-semibold uppercase tracking-wide text-slate-400">{section.title}</div>
              {section.links.map((link) => (
                <NavLink key={link.to} to={link.to}
                  className={({ isActive }) => cx('block rounded-md px-2 py-1.5 text-sm',
                    isActive ? 'bg-brand-50 font-medium text-brand-700' : 'text-slate-700 hover:bg-slate-100')}>
                  {link.label}
                </NavLink>
              ))}
            </div>
          ))}
        </nav>
      </aside>
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-end gap-3 border-b border-slate-200 bg-white px-6 py-2">
          <span className="text-sm text-slate-600">{user?.name}</span>
          <Button variant="secondary" onClick={() => void logout()}>Sair</Button>
        </header>
        <main className="flex-1 p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

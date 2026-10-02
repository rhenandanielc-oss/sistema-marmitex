import { forwardRef, useEffect, type ButtonHTMLAttributes, type InputHTMLAttributes, type ReactNode,
  type SelectHTMLAttributes, type TextareaHTMLAttributes } from 'react'

export function cx(...classes: (string | false | null | undefined)[]): string {
  return classes.filter(Boolean).join(' ')
}

type Variant = 'primary' | 'secondary' | 'danger' | 'ghost'

const VARIANTS: Record<Variant, string> = {
  primary: 'bg-brand-600 text-white hover:bg-brand-700 disabled:bg-brand-500/60',
  secondary: 'bg-white text-slate-700 border border-slate-300 hover:bg-slate-50',
  danger: 'bg-red-600 text-white hover:bg-red-700',
  ghost: 'text-brand-600 hover:bg-brand-50',
}

export function Button({ variant = 'primary', className, ...props }: ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: Variant
}) {
  return (
    <button
      type="button"
      className={cx('inline-flex items-center justify-center gap-1 rounded-md px-3 py-2 text-sm font-medium',
        'transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 disabled:cursor-not-allowed',
        VARIANTS[variant], className)}
      {...props}
    />
  )
}

export function Field({ label, error, hint, children, htmlFor, required }: {
  label: string
  error?: string
  hint?: string
  children: ReactNode
  htmlFor?: string
  required?: boolean
}) {
  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={htmlFor} className="text-sm font-medium text-slate-700">
        {label}
        {required && <span className="text-red-600"> *</span>}
      </label>
      {children}
      {hint && !error && <span className="text-xs text-slate-500">{hint}</span>}
      {error && <span role="alert" className="text-xs text-red-600">{error}</span>}
    </div>
  )
}

const inputClass = 'rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm ' +
  'focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 disabled:bg-slate-100'

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  function Input({ className, ...props }, ref) {
    return <input ref={ref} className={cx(inputClass, className)} {...props} />
  },
)

export const Select = forwardRef<HTMLSelectElement, SelectHTMLAttributes<HTMLSelectElement>>(
  function Select({ className, ...props }, ref) {
    return <select ref={ref} className={cx(inputClass, className)} {...props} />
  },
)

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaHTMLAttributes<HTMLTextAreaElement>>(
  function Textarea({ className, ...props }, ref) {
    return <textarea ref={ref} rows={2} className={cx(inputClass, className)} {...props} />
  },
)

export function Card({ title, actions, children, className }: {
  title?: ReactNode
  actions?: ReactNode
  children: ReactNode
  className?: string
}) {
  return (
    <section className={cx('rounded-lg border border-slate-200 bg-white shadow-sm', className)}>
      {(title || actions) && (
        <header className="flex items-center justify-between gap-2 border-b border-slate-100 px-4 py-3">
          <h2 className="text-sm font-semibold text-slate-800">{title}</h2>
          {actions}
        </header>
      )}
      <div className="p-4">{children}</div>
    </section>
  )
}

export function PageHeader({ title, subtitle, actions }: { title: string; subtitle?: ReactNode; actions?: ReactNode }) {
  return (
    <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 className="text-xl font-semibold text-slate-900">{title}</h1>
        {subtitle && <p className="mt-1 text-sm text-slate-500">{subtitle}</p>}
      </div>
      {actions && <div className="flex gap-2">{actions}</div>}
    </div>
  )
}

const BADGE_TONES = {
  green: 'bg-emerald-50 text-emerald-700 ring-emerald-600/20',
  gray: 'bg-slate-100 text-slate-600 ring-slate-500/20',
  blue: 'bg-brand-50 text-brand-700 ring-brand-600/20',
  amber: 'bg-amber-50 text-amber-800 ring-amber-600/20',
  red: 'bg-red-50 text-red-700 ring-red-600/20',
}

export function Badge({ tone = 'gray', children }: { tone?: keyof typeof BADGE_TONES; children: ReactNode }) {
  return (
    <span className={cx('inline-flex items-center whitespace-nowrap rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset',
      BADGE_TONES[tone])}>
      {children}
    </span>
  )
}

export function ActiveBadge({ active }: { active: boolean }) {
  return active ? <Badge tone="green">Ativo</Badge> : <Badge tone="gray">Inativo</Badge>
}

export function Modal({ open, title, onClose, children, footer, wide }: {
  open: boolean
  title: string
  onClose: () => void
  children: ReactNode
  footer?: ReactNode
  wide?: boolean
}) {
  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onClose])
  if (!open) return null
  return (
    <div className="fixed inset-0 z-40 flex items-start justify-center overflow-y-auto bg-slate-900/40 p-4 pt-16">
      <div role="dialog" aria-modal="true" aria-label={title}
        className={cx('w-full rounded-lg bg-white shadow-xl', wide ? 'max-w-3xl' : 'max-w-lg')}>
        <div className="flex items-center justify-between border-b border-slate-100 px-5 py-3">
          <h2 className="text-base font-semibold text-slate-900">{title}</h2>
          <button type="button" aria-label="Fechar" onClick={onClose} className="text-slate-400 hover:text-slate-700">✕</button>
        </div>
        <div className="px-5 py-4">{children}</div>
        {footer && <div className="flex justify-end gap-2 border-t border-slate-100 px-5 py-3">{footer}</div>}
      </div>
    </div>
  )
}

export function ConfirmDialog({ open, title, message, confirmLabel = 'Confirmar', danger, onConfirm, onCancel, busy }: {
  open: boolean
  title: string
  message: ReactNode
  confirmLabel?: string
  danger?: boolean
  onConfirm: () => void
  onCancel: () => void
  busy?: boolean
}) {
  return (
    <Modal open={open} title={title} onClose={onCancel} footer={
      <>
        <Button variant="secondary" onClick={onCancel}>Cancelar</Button>
        <Button variant={danger ? 'danger' : 'primary'} onClick={onConfirm} disabled={busy}>{confirmLabel}</Button>
      </>
    }>
      <p className="text-sm text-slate-700">{message}</p>
    </Modal>
  )
}

export function Pagination({ page, pages, total, onChange }: {
  page: number
  pages: number
  total: number
  onChange: (page: number) => void
}) {
  return (
    <div className="mt-3 flex items-center justify-between text-sm text-slate-600">
      <span>{total} registro(s)</span>
      <div className="flex items-center gap-2">
        <Button variant="secondary" disabled={page <= 1} onClick={() => onChange(page - 1)}>Anterior</Button>
        <span>Página {pages === 0 ? 0 : page} de {pages}</span>
        <Button variant="secondary" disabled={page >= pages} onClick={() => onChange(page + 1)}>Próxima</Button>
      </div>
    </div>
  )
}

export function EmptyState({ children }: { children: ReactNode }) {
  return <div className="rounded-md border border-dashed border-slate-300 p-6 text-center text-sm text-slate-500">{children}</div>
}

export function Loading() {
  return <div className="p-4 text-sm text-slate-500">Carregando…</div>
}

export function ErrorBox({ message }: { message: string }) {
  return <div role="alert" className="rounded-md bg-red-50 p-3 text-sm text-red-700">{message}</div>
}

export function Th({ children, className, onClick, sorted }: {
  children?: ReactNode
  className?: string
  onClick?: () => void
  sorted?: 'asc' | 'desc' | null
}) {
  return (
    <th scope="col" className={cx('px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-slate-500',
      onClick && 'cursor-pointer select-none hover:text-slate-800', className)} onClick={onClick}>
      {children}
      {sorted === 'asc' && ' ▲'}
      {sorted === 'desc' && ' ▼'}
    </th>
  )
}

export function Td({ children, className }: { children?: ReactNode; className?: string }) {
  return <td className={cx('px-3 py-2 text-sm text-slate-700', className)}>{children}</td>
}

export function Table({ children }: { children: ReactNode }) {
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-slate-200">{children}</table>
    </div>
  )
}

import { DELIVERY_TYPE_LABELS, PAYMENT_STATUS_LABELS } from '../lib/format'
import { Badge } from './ui'

export function PaymentBadge({ status }: { status: string }) {
  return status === 'PAGO' ? <Badge tone="green">✓ {PAYMENT_STATUS_LABELS.PAGO}</Badge>
    : <Badge tone="amber">{PAYMENT_STATUS_LABELS.PENDENTE}</Badge>
}

export function DeliveryBadge({ type }: { type: string }) {
  return <Badge tone="gray">{DELIVERY_TYPE_LABELS[type] ?? type}</Badge>
}

export const DELIVERY_OPTIONS = [
  { value: 'OBRA', label: 'Obra (entregue na obra)' },
  { value: 'ENTREGA', label: 'Entrega (outro endereço)' },
  { value: 'RETIRADA', label: 'Retirada (cliente busca)' },
] as const

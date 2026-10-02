from enum import StrEnum


class Role(StrEnum):
    ADMIN = "ADMIN"


class CostType(StrEnum):
    CUSTO_DIARIO = "CUSTO_DIARIO"
    CUSTO_FIXO = "CUSTO_FIXO"


class BuyerType(StrEnum):
    COMPANY = "COMPANY"
    CUSTOMER = "CUSTOMER"


class CompanyBillingCycle(StrEnum):
    QUINZENAL = "QUINZENAL"
    MENSAL = "MENSAL"


class CustomerBillingCycle(StrEnum):
    A_VISTA = "A_VISTA"
    SEMANAL = "SEMANAL"
    QUINZENAL = "QUINZENAL"
    MENSAL = "MENSAL"


class AuditAction(StrEnum):
    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    LOGIN_FAILED = "LOGIN_FAILED"
    LOGOUT = "LOGOUT"
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    ACTIVATE = "ACTIVATE"
    DEACTIVATE = "DEACTIVATE"
    DELETE = "DELETE"
    PASSWORD_CHANGE = "PASSWORD_CHANGE"

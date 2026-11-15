"""
Модели данных для учёта договоров, работ и платежей.

Используются dataclass с точными типами (Decimal, date, Optional).
Все денежные суммы представлены через Decimal для исключения ошибок округления.
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class Contract:
    """Договор с подрядчиком на общую сумму."""
    contract_id: str
    contractor: str
    amount: Decimal
    signed_at: date


@dataclass(frozen=True)
class Work:
    """Работа по договору со статусом и датами завершения/отмены."""
    work_id: str
    contract_id: str
    title: str
    price: Decimal
    status: str
    completed_at: Optional[date] = None
    cancelled_at: Optional[date] = None


@dataclass(frozen=True)
class Payment:
    """Платёж по договору или конкретной работе со статусом движения средств."""
    payment_id: str
    contract_id: str
    work_id: Optional[str]
    purpose: str
    amount: Decimal
    status: str
    created_at: date
    paid_at: Optional[date] = None
    refunded_at: Optional[date] = None


@dataclass
class WorkReportItem:
    """Строка отчёта по конкретной работе."""
    work_id: str
    contract_id: str
    title: str
    price: Decimal
    paid_amount: Decimal
    remaining_amount: Decimal
    status_on_date: str


@dataclass
class ContractReportItem:
    """Сводная строка отчёта по договору в целом."""
    contract_id: str
    contractor: str
    contract_amount: Decimal
    works_price_total: Decimal
    paid_total: Decimal
    remaining_total: Decimal
    unallocated_advance: Decimal

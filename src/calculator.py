"""
Логика расчёта оплат и распределения авансов по работам и договорам.

Алгоритм:
  1. Определение статуса работ на целевую дату (done/cancelled/planned).
  2. Фильтрация фактически проведённых оплат на дату (paid_at <= target_date).
  3. Первоочередное распределение целевых платежей с явным work_id.
  4. Распределение общих авансов по договору методом FIFO:
     сначала покрываются фактически принятые работы (done) по дате завершения,
     затем запланированные (planned) по порядку заведения.
  5. Отменённые работы исключаются из начисления долга и распределения авансов.
"""

from datetime import date
from decimal import Decimal
from typing import Dict, List, Tuple

from src.models import (
    Contract,
    ContractReportItem,
    Payment,
    Work,
    WorkReportItem,
)


def get_work_status_on_date(work: Work, target_date: date) -> str:
    """Определяет исторический статус работы на конкретную дату."""
    if work.cancelled_at and work.cancelled_at <= target_date:
        return "cancelled"
    if work.completed_at and work.completed_at <= target_date:
        return "done"
    return "planned"


def is_payment_effective_on_date(p: Payment, target_date: date) -> bool:
    """Проверяет, является ли платёж фактически проведённым и не возвращённым на дату."""
    if p.status == "queued" or not p.paid_at:
        return False
    if p.paid_at > target_date:
        return False
    if p.status == "refunded" and p.refunded_at and p.refunded_at <= target_date:
        return False
    return True


def apply_direct_payments(
    works: List[Work],
    payments: List[Payment]
) -> Tuple[Dict[str, Decimal], List[Payment]]:
    """Применяет прямые платежи (с указанным work_id) к соответствующим работам."""
    work_paid: Dict[str, Decimal] = {w.work_id: Decimal("0.00") for w in works}
    unallocated_payments: List[Payment] = []
    for p in payments:
        if p.work_id and p.work_id in work_paid:
            work_paid[p.work_id] += p.amount
        else:
            unallocated_payments.append(p)
    return work_paid, unallocated_payments


def sort_works_for_allocation(works: List[Work], target_date: date) -> List[Work]:
    """Сортирует работы для распределения аванса: сначала done по дате, затем planned."""
    def sort_key(w: Work) -> Tuple[int, date, str]:
        status = get_work_status_on_date(w, target_date)
        if status == "done":
            return (0, w.completed_at or target_date, w.work_id)
        return (1, date.max, w.work_id)

    active_works = [w for w in works if get_work_status_on_date(w, target_date) != "cancelled"]
    return sorted(active_works, key=sort_key)


def allocate_general_advances(
    works: List[Work],
    work_paid: Dict[str, Decimal],
    general_pool: Decimal,
    target_date: date
) -> Tuple[Dict[str, Decimal], Decimal]:
    """Распределяет общий пул авансов по активным работам методом FIFO."""
    sorted_works = sort_works_for_allocation(works, target_date)
    remaining_pool = general_pool
    for w in sorted_works:
        if remaining_pool <= Decimal("0.00"):
            break
        current_paid = work_paid.get(w.work_id, Decimal("0.00"))
        need = max(Decimal("0.00"), w.price - current_paid)
        alloc = min(need, remaining_pool)
        work_paid[w.work_id] = current_paid + alloc
        remaining_pool -= alloc
    return work_paid, remaining_pool


def calculate_report_for_contract(
    contract: Contract,
    works: List[Work],
    payments: List[Payment],
    target_date: date
) -> Tuple[List[WorkReportItem], ContractReportItem]:
    """Строит детальный отчёт по работам и итоговый отчёт по одному договору."""
    effective_payments = [p for p in payments if is_payment_effective_on_date(p, target_date)]
    work_paid, general_payments = apply_direct_payments(works, effective_payments)
    general_pool = sum((p.amount for p in general_payments), Decimal("0.00"))
    work_paid, unallocated_advance = allocate_general_advances(
        works, work_paid, general_pool, target_date
    )
    work_items = build_work_items(works, work_paid, target_date)
    contract_item = build_contract_summary(
        contract, work_items, effective_payments, unallocated_advance
    )
    return work_items, contract_item


def build_work_items(
    works: List[Work],
    work_paid: Dict[str, Decimal],
    target_date: date
) -> List[WorkReportItem]:
    """Формирует список строк отчёта по каждой работе договора."""
    items: List[WorkReportItem] = []
    for w in works:
        status = get_work_status_on_date(w, target_date)
        paid = work_paid.get(w.work_id, Decimal("0.00"))
        effective_price = Decimal("0.00") if status == "cancelled" else w.price
        remaining = max(Decimal("0.00"), effective_price - paid)
        items.append(WorkReportItem(
            work_id=w.work_id,
            contract_id=w.contract_id,
            title=w.title,
            price=effective_price,
            paid_amount=paid,
            remaining_amount=remaining,
            status_on_date=status
        ))
    return items


def build_contract_summary(
    contract: Contract,
    work_items: List[WorkReportItem],
    effective_payments: List[Payment],
    unallocated_advance: Decimal
) -> ContractReportItem:
    """Формирует итоговую сводную запись по договору."""
    total_works_price = sum((w.price for w in work_items), Decimal("0.00"))
    total_paid = sum((p.amount for p in effective_payments), Decimal("0.00"))
    total_remaining = sum((w.remaining_amount for w in work_items), Decimal("0.00"))
    return ContractReportItem(
        contract_id=contract.contract_id,
        contractor=contract.contractor,
        contract_amount=contract.amount,
        works_price_total=total_works_price,
        paid_total=total_paid,
        remaining_total=total_remaining,
        unallocated_advance=unallocated_advance
    )

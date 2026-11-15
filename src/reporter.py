"""
Форматирование отчёта в консоль и экспорт в CSV.

Предоставляет читаемый табличный вывод с разделением по договорам,
детализацией по работам и сводными итогами.
"""

import csv
from decimal import Decimal
from pathlib import Path
from typing import List, Tuple

from src.models import ContractReportItem, WorkReportItem


def format_rub(amount: Decimal) -> str:
    """Форматирует Decimal сумму в читаемый денежный формат с разделителями."""
    return f"{amount:,.2f} ₽".replace(",", " ")


def print_cli_report(
    reports: List[Tuple[List[WorkReportItem], ContractReportItem]],
    target_date_str: str
) -> None:
    """Выводит отчёт в терминал в виде структурированной таблицы."""
    print("=" * 86)
    print(f" ОТЧЁТ ПО ВЫПОЛНЕНИЮ И ОПЛАТЕ РАБОТ ПО ДОГОВОРАМ НА ДАТУ: {target_date_str}")
    print("=" * 86)
    for work_items, summary in reports:
        print_contract_header(summary)
        print_work_table(work_items)
        print_contract_summary(summary)
        print("-" * 86)


def print_contract_header(s: ContractReportItem) -> None:
    """Выводит шапку с реквизитами договора."""
    print(f"\nДоговор: {s.contract_id} | Подрядчик: {s.contractor}")
    print(f"Сумма по договору: {format_rub(s.contract_amount)}")


def print_work_table(items: List[WorkReportItem]) -> None:
    """Выводит таблицу работ договора."""
    header = f"{'ID':<6} | {'Статус':<10} | {'Стоимость':>14} | {'Выплачено':>14} | {'Осталось':>14} | {'Название'}"
    print("-" * 86)
    print(header)
    print("-" * 86)
    for it in items:
        price_s = format_rub(it.price)
        paid_s = format_rub(it.paid_amount)
        rem_s = format_rub(it.remaining_amount)
        print(f"{it.work_id:<6} | {it.status_on_date:<10} | {price_s:>14} | {paid_s:>14} | {rem_s:>14} | {it.title}")


def print_contract_summary(s: ContractReportItem) -> None:
    """Выводит блок итогов по договору."""
    print("-" * 86)
    print(f"ИТОГО по работам:  {format_rub(s.works_price_total):>14} | Оплачено: {format_rub(s.paid_total):>14} | К доплате: {format_rub(s.remaining_total):>14}")
    if s.unallocated_advance > Decimal("0.00"):
        print(f"  * Неизрасходованный свободный аванс договора: {format_rub(s.unallocated_advance)}")


def export_reports_to_csv(
    reports: List[Tuple[List[WorkReportItem], ContractReportItem]],
    works_output: Path,
    contracts_output: Path
) -> None:
    """Экспортирует результаты расчёта в CSV-файлы."""
    export_works_csv(reports, works_output)
    export_contracts_csv(reports, contracts_output)


def export_works_csv(
    reports: List[Tuple[List[WorkReportItem], ContractReportItem]],
    path: Path
) -> None:
    """Записывает детализацию по работам в CSV."""
    with open(path, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["contract_id", "work_id", "title", "status_on_date", "price", "paid_amount", "remaining_amount"])
        for works, _ in reports:
            for w in works:
                writer.writerow([w.contract_id, w.work_id, w.title, w.status_on_date, f"{w.price:.2f}", f"{w.paid_amount:.2f}", f"{w.remaining_amount:.2f}"])


def export_contracts_csv(
    reports: List[Tuple[List[WorkReportItem], ContractReportItem]],
    path: Path
) -> None:
    """Записывает сводные итоги по договорам в CSV."""
    with open(path, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["contract_id", "contractor", "contract_amount", "works_price_total", "paid_total", "remaining_total", "unallocated_advance"])
        for _, s in reports:
            writer.writerow([s.contract_id, s.contractor, f"{s.contract_amount:.2f}", f"{s.works_price_total:.2f}", f"{s.paid_total:.2f}", f"{s.remaining_total:.2f}", f"{s.unallocated_advance:.2f}"])

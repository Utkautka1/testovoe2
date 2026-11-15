#!/usr/bin/env python3
"""
Точка входа CLI программы расчёта авансов и взаиморасчётов по договорам.

Запуск:
  python3 solution.py [--date YYYY-MM-DD] [--data-dir PATH] [--csv-out DIR]
"""

import argparse
import sys
from datetime import date, datetime
from pathlib import Path
from typing import List, Tuple

from src.calculator import calculate_report_for_contract
from src.loader import load_contracts, load_payments, load_works
from src.models import (
    Contract,
    ContractReportItem,
    Payment,
    Work,
    WorkReportItem,
)
from src.reporter import export_reports_to_csv, print_cli_report


def build_arg_parser() -> argparse.ArgumentParser:
    """Создаёт конфигурацию аргументов командной строки."""
    parser = argparse.ArgumentParser(
        description="Расчёт оплат и остатков по работам и договорам на заданную дату."
    )
    parser.add_argument(
        "--date", type=str, default="2026-11-10",
        help="Дата отчёта в формате YYYY-MM-DD (по умолчанию: 2026-11-10)"
    )
    parser.add_argument(
        "--data-dir", type=Path, default=Path("candidate-B/data"),
        help="Путь к директории с исходными CSV файлами"
    )
    parser.add_argument(
        "--csv-out", type=Path, default=None,
        help="Директория для сохранения отчётов в CSV (опционально)"
    )
    return parser


def compute_all_reports(
    contracts: List[Contract],
    all_works: List[Work],
    all_payments: List[Payment],
    target_date: date
) -> List[Tuple[List[WorkReportItem], ContractReportItem]]:
    """Строит отчёты по каждому договору."""
    reports: List[Tuple[List[WorkReportItem], ContractReportItem]] = []

    for contract in contracts:
        c_works = [w for w in all_works if w.contract_id == contract.contract_id]
        c_payments = [p for p in all_payments if p.contract_id == contract.contract_id]
        reports.append(calculate_report_for_contract(contract, c_works, c_payments, target_date))

    return reports


def run_pipeline(data_dir: Path, target_date_str: str, csv_out: Path | None) -> None:
    """Оркестрирует загрузку данных, расчёт и вывод результатов."""
    target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()

    contracts = load_contracts(data_dir / "contracts.csv")
    all_works = load_works(data_dir / "works.csv")
    all_payments = load_payments(data_dir / "payments.csv")

    reports = compute_all_reports(contracts, all_works, all_payments, target_date)
    print_cli_report(reports, target_date_str)

    if csv_out:
        save_csv_results(reports, csv_out, target_date_str)


def save_csv_results(
    reports: List[Tuple[List[WorkReportItem], ContractReportItem]],
    csv_out: Path,
    date_str: str
) -> None:
    """Сохраняет отчёты по работам и договорам в указанную папку."""
    csv_out.mkdir(parents=True, exist_ok=True)

    w_path = csv_out / f"report_works_{date_str}.csv"
    c_path = csv_out / f"report_contracts_{date_str}.csv"

    export_reports_to_csv(reports, w_path, c_path)
    print(f"\n[OK] CSV-отчёты сохранены в: {csv_out.resolve()}")


def main() -> None:
    """Основная функция запуска."""
    parser = build_arg_parser()
    args = parser.parse_args()

    try:
        run_pipeline(args.data_dir, args.date, args.csv_out)
    except Exception as e:
        print(f"Ошибка выполнения: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

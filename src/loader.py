"""
Загрузка и парсинг CSV файлов выгрузки учёта.

Чтение файлов contracts.csv, works.csv, payments.csv с преобразованием
строковых значений в типизированные объекты Contract, Work, Payment.
"""

import csv
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.models import Contract, Payment, Work


def parse_date(date_str: str) -> Optional[date]:
    """Парсит дату формата YYYY-MM-DD или возвращает None для пустой строки."""
    clean_val = date_str.strip()
    return datetime.strptime(clean_val, "%Y-%m-%d").date() if clean_val else None


def parse_contract_row(row: Dict[str, Any]) -> Contract:
    """Преобразует строку CSV в объект Contract."""
    return Contract(
        contract_id=row["contract_id"].strip(),
        contractor=row["contractor"].strip(),
        amount=Decimal(row["amount"].strip()),
        signed_at=datetime.strptime(row["signed_at"].strip(), "%Y-%m-%d").date()
    )


def load_contracts(csv_path: Path) -> List[Contract]:
    """Читает contracts.csv и возвращает список договоров."""
    with open(csv_path, mode="r", encoding="utf-8") as f:
        return [parse_contract_row(row) for row in csv.DictReader(f)]


def parse_work_row(row: Dict[str, Any]) -> Work:
    """Преобразует строку CSV в объект Work."""
    return Work(
        work_id=row["work_id"].strip(),
        contract_id=row["contract_id"].strip(),
        title=row["title"].strip(),
        price=Decimal(row["price"].strip()),
        status=row["status"].strip(),
        completed_at=parse_date(row.get("completed_at", "")),
        cancelled_at=parse_date(row.get("cancelled_at", ""))
    )


def load_works(csv_path: Path) -> List[Work]:
    """Читает works.csv и возвращает список работ."""
    with open(csv_path, mode="r", encoding="utf-8") as f:
        return [parse_work_row(row) for row in csv.DictReader(f)]


def parse_payment_row(row: Dict[str, Any]) -> Payment:
    """Преобразует строку CSV в объект Payment."""
    raw_work_id = row.get("work_id", "").strip()

    return Payment(
        payment_id=row["payment_id"].strip(),
        contract_id=row["contract_id"].strip(),
        work_id=raw_work_id if raw_work_id else None,
        purpose=row.get("purpose", "").strip(),
        amount=Decimal(row["amount"].strip()),
        status=row["status"].strip(),
        created_at=datetime.strptime(row["created_at"].strip(), "%Y-%m-%d").date(),
        paid_at=parse_date(row.get("paid_at", "")),
        refunded_at=parse_date(row.get("refunded_at", ""))
    )


def load_payments(csv_path: Path) -> List[Payment]:
    """Читает payments.csv и возвращает список платежей."""
    with open(csv_path, mode="r", encoding="utf-8") as f:
        return [parse_payment_row(row) for row in csv.DictReader(f)]

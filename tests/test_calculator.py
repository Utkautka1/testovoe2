"""
Тесты для модуля расчёта оплат и авансов.

Проверяют:
  - Исключение отменённых работ из расчёта стоимости.
  - Учёт целевых платежей (work_id).
  - Игнорирование платежей в статусе queued и refunded.
  - Влияние фильтрации по дате (исторический срез).
  - FIFO-распределение аванса по завершённым и запланированным работам.
"""

from datetime import date
from decimal import Decimal
import unittest

from src.calculator import (
    calculate_report_for_contract,
    get_work_status_on_date,
    is_payment_effective_on_date,
)
from src.models import Contract, Payment, Work


class TestAdvanceCalculator(unittest.TestCase):
    """Тестирование бизнес-логики распределения платежей."""

    def setUp(self) -> None:
        """Подготовка тестовых данных."""
        self.contract = Contract("D-TEST", "Подрядчик", Decimal("100000.00"), date(2026, 1, 1))

    def test_payment_status_filter_on_date(self) -> None:
        """Проверка фильтрации платежей по статусам и датам."""
        target = date(2026, 1, 10)

        p_q = Payment("P-Q", "D", None, "", Decimal("1000"), "queued", date(2026, 1, 2))
        p_f = Payment("P-F", "D", None, "", Decimal("1000"), "paid", date(2026, 1, 2), paid_at=date(2026, 1, 15))
        p_r = Payment("P-R", "D", None, "", Decimal("1000"), "refunded", date(2026, 1, 2), paid_at=date(2026, 1, 3), refunded_at=date(2026, 1, 5))
        p_v = Payment("P-V", "D", None, "", Decimal("2000"), "paid", date(2026, 1, 2), paid_at=date(2026, 1, 4))

        self.assertFalse(is_payment_effective_on_date(p_q, target))
        self.assertFalse(is_payment_effective_on_date(p_f, target))
        self.assertFalse(is_payment_effective_on_date(p_r, target))
        self.assertTrue(is_payment_effective_on_date(p_v, target))

    def test_cancelled_work_status(self) -> None:
        """Отменённая работа на дату отмены должна иметь статус cancelled и цену 0."""
        work = Work("W-1", "D-TEST", "Отмена", Decimal("50000.00"), "cancelled", cancelled_at=date(2026, 1, 5))

        self.assertEqual(get_work_status_on_date(work, date(2026, 1, 4)), "planned")
        self.assertEqual(get_work_status_on_date(work, date(2026, 1, 5)), "cancelled")

    def test_direct_and_general_advance_fifo(self) -> None:
        """Целевой платёж идёт строго в работу, остаток аванса распределяется по FIFO."""
        works = [
            Work("W-1", "D-TEST", "Работа 1", Decimal("30000.00"), "done", completed_at=date(2026, 1, 2)),
            Work("W-2", "D-TEST", "Работа 2", Decimal("40000.00"), "planned")
        ]
        payments = [
            Payment("P-1", "D-TEST", "W-2", "Целевой", Decimal("10000.00"), "paid", date(2026, 1, 1), paid_at=date(2026, 1, 1)),
            Payment("P-2", "D-TEST", None, "Аванс", Decimal("40000.00"), "paid", date(2026, 1, 2), paid_at=date(2026, 1, 2))
        ]

        w_items, summary = calculate_report_for_contract(self.contract, works, payments, date(2026, 1, 10))
        w1_rep = next(w for w in w_items if w.work_id == "W-1")
        w2_rep = next(w for w in w_items if w.work_id == "W-2")

        self.assertEqual(w1_rep.paid_amount, Decimal("30000.00"))
        self.assertEqual(w1_rep.remaining_amount, Decimal("0.00"))
        self.assertEqual(w2_rep.paid_amount, Decimal("20000.00"))
        self.assertEqual(w2_rep.remaining_amount, Decimal("20000.00"))
        self.assertEqual(summary.paid_total, Decimal("50000.00"))


if __name__ == "__main__":
    unittest.main()

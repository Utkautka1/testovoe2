# Архитектура проекта и UML-диаграмма

## Описание системы
Программа строит отчёт по взаиморасчётам с подрядчиками на заданную дату. Модули разделены по принципу единой ответственности (SRP) и используют строгую типизацию (`Decimal`, `dataclass`).

```mermaid
classDiagram
    direction TB

    class Contract {
        +str contract_id
        +str contractor
        +Decimal amount
        +date signed_at
    }

    class Work {
        +str work_id
        +str contract_id
        +str title
        +Decimal price
        +str status
        +date completed_at
        +date cancelled_at
    }

    class Payment {
        +str payment_id
        +str contract_id
        +str work_id
        +str purpose
        +Decimal amount
        +str status
        +date created_at
        +date paid_at
        +date refunded_at
    }

    class WorkReportItem {
        +str work_id
        +str contract_id
        +str title
        +Decimal price
        +Decimal paid_amount
        +Decimal remaining_amount
        +str status_on_date
    }

    class ContractReportItem {
        +str contract_id
        +str contractor
        +Decimal contract_amount
        +Decimal works_price_total
        +Decimal paid_total
        +Decimal remaining_total
        +Decimal unallocated_advance
    }

    class DataLoader {
        +load_contracts(path) List~Contract~
        +load_works(path) List~Work~
        +load_payments(path) List~Payment~
        +parse_date(str) date
    }

    class AdvanceCalculator {
        +get_work_status_on_date(work, target_date) str
        +is_payment_effective_on_date(payment, target_date) bool
        +apply_direct_payments(works, payments) Tuple
        +sort_works_for_allocation(works, target_date) List~Work~
        +allocate_general_advances(works, work_paid, pool, target_date) Tuple
        +calculate_report_for_contract(contract, works, payments, target_date) Tuple
        +build_work_items(works, work_paid, target_date) List~WorkReportItem~
        +build_contract_summary(contract, work_items, payments, unallocated) ContractReportItem
    }

    class Reporter {
        +format_rub(amount) str
        +print_cli_report(reports, date_str) void
        +export_reports_to_csv(reports, works_path, contracts_path) void
    }

    Contract "1" *-- "*" Work : contains
    Contract "1" *-- "*" Payment : has
    DataLoader ..> Contract : creates
    DataLoader ..> Work : creates
    DataLoader ..> Payment : creates
    AdvanceCalculator ..> WorkReportItem : generates
    AdvanceCalculator ..> ContractReportItem : generates
    Reporter ..> WorkReportItem : renders
    Reporter ..> ContractReportItem : renders
```

## Пайплайн обработки данных

```mermaid
flowchart TD
    A["CSV файлы (data/)"] --> B["DataLoader (src/loader.py)"]
    B --> C["Модели данных (src/models.py)"]
    C --> D["AdvanceCalculator (src/calculator.py)"]
    T["Целевая дата (--date)"] --> D
    D --> E["1. Определение исторического статуса работ"]
    D --> F["2. Фильтрация проведённых оплат на дату"]
    D --> G["3. Зачёт прямых платежей (work_id)"]
    D --> H["4. FIFO-распределение общего аванса договора"]
    E --> I["Итоговые WorkReportItem и ContractReportItem"]
    F --> I
    G --> I
    H --> I
    I --> J["Reporter (src/reporter.py)"]
    J --> K["Вывод таблицы в терминал"]
    J --> L["Экспорт в CSV (при --csv-out)"]
```

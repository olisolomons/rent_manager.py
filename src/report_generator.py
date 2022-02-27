import abc
import operator
import typing
from datetime import date

from pathlib import Path
from rent_manager.state.other_transaction import TransactionReason, OtherTransaction
from rent_manager.state.rent_payment import RentPayment
from typing import Sequence

from fpdf import FPDF, HTMLMixin

from rent_manager.state.rent_manager_state import RentManagerState, RentCalculations, RentManagerMainState


class PDF(FPDF, HTMLMixin):
    pass


def hello_world():
    gen = PDFGenerator()
    data = [[str(i), f'{i**2=}', ' ' + 'a' * i] for i in range(5)]
    gen.put_table(['Head 1', 'Head 2', 'Head 3'], data)
    gen.output('hello_world.pdf')


class PDFGenerator:
    def __init__(self):
        self.pdf = PDF()
        self.pdf.add_page()
        self.pdf.set_font('helvetica', size=12)

        self.html_buffer = []

    def put(self, html_fragment):
        self.html_buffer.append(html_fragment)

    def tag(self, tag_name: str, **attributes: str):
        return AutoClosingTag(self, tag_name, **attributes)

    def put_table(self, headers: Sequence[str | tuple[str, float]], data):
        with self.tag('table', border='1'):
            with self.tag('thead'):
                with self.tag('tr', bgcolor='#d8e1ed'):
                    def get_weight(header):
                        return 1 if isinstance(header, str) else header[1]

                    total_weight = sum(get_weight(header) for header in headers)
                    widths = [int(get_weight(header) / total_weight * 100) for header in headers]
                    shortfall = 100 - sum(widths)
                    for i in range(shortfall):
                        widths[i] += 1

                    for header, width in zip(headers, widths):
                        with self.tag('th', width=f'{width}%'):
                            if isinstance(header, str):
                                self.put(header)
                            else:
                                self.put(header[0])
            with self.tag('tbody'):
                # TODO: wrap long lines into multiple rows
                for i, row in enumerate(data):
                    with self.tag('tr', bgcolor='#FFFFFF' if i % 2 == 0 else '#e9eef5'):
                        for cell in row:
                            with self.tag('td'):
                                self.put(cell)

    def output(self, path):
        self.pdf.write_html(''.join(self.html_buffer))
        self.pdf.output(path)


class AutoClosingTag:
    def __init__(self, report_generator: PDFGenerator, tag_name: str, **attributes: str):
        self.report_generator = report_generator
        self.tag_name = tag_name
        self.attributes = attributes

    def __enter__(self):
        attributes_string = ''.join(f' {key}="{value}"' for key, value in self.attributes.items())
        self.report_generator.put(f'<{self.tag_name}{attributes_string}>')

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.report_generator.put(f'</{self.tag_name}>')


def format_currency(amount, symbol='£'):
    return f'{symbol}{amount / 100:.2f}'


def generate_report(data: RentManagerState, calculations: RentCalculations, export_path: str | Path):
    pdf = PDFGenerator()
    with pdf.tag('h1'):
        pdf.put('Summary')

    non_payment_costs = format_currency(
        calculations.total_costs - calculations.other_transaction_sums[TransactionReason.Payment]
    )
    total_payments = format_currency(calculations.other_transaction_sums[TransactionReason.Payment])
    pdf.put_table(
        [' ', 'Amount'],
        [
            ['Total rent received', format_currency(calculations.total_rent_received)],
            ['Costs', non_payment_costs],
            ['Payments to landlord', total_payments],
            ['Balance',
             f'{format_currency(calculations.total_rent_received)} - {non_payment_costs} - {total_payments} = '
             f'{format_currency(calculations.balance)}']
        ]
    )

    date_format = '%d/%m/%Y'
    month_format = '%b %Y'
    with pdf.tag('h1'):
        pdf.put('Payments to landlord')
    transaction: OtherTransaction
    pdf.put_table(
        ['Date', 'Amount'],
        [[transaction._date.strftime(date_format), format_currency(transaction.amount)]
         for transaction in data.rent_manager_main_state.other_transactions
         if transaction.reason is TransactionReason.Payment]
    )

    with pdf.tag('h1'):
        pdf.put('Rent received per month')

    rent_for_months = []
    for month, paid in calculations.rent_for_months:
        month_arrears = data.rent_arrangement_data.monthly_rent - paid
        if month_arrears == 0:
            color = '00AA00'
        elif month_arrears > 0:
            color = 'DAD000'
        else:
            color = 'AA0000'
        rent_for_months.append([
            month.strftime(month_format), format_currency(paid),
            f'<font color="#{color}">' + format_currency(month_arrears) + '</font>'
        ])
    pdf.put_table(
        ['Month', 'Amount Paid', 'Arrears for month'],
        rent_for_months
    )

    class AnyTransaction(abc.ABC):
        @property
        @abc.abstractmethod
        def date(self) -> date:
            pass

        @property
        @abc.abstractmethod
        def type(self) -> str:
            pass

        @property
        @abc.abstractmethod
        def amount(self) -> int:
            pass

        @property
        @abc.abstractmethod
        def comment(self) -> str:
            pass

    class AnyTransactionOtherTransaction(AnyTransaction):
        def __init__(self, inner: OtherTransaction) -> None:
            super().__init__()
            self.inner: OtherTransaction = inner

        @property
        def date(self) -> date:
            return self.inner._date

        @property
        def type(self) -> str:
            return self.inner.reason.readable_name()

        @property
        def amount(self) -> int:
            return self.inner.amount

        @property
        def comment(self) -> str:
            return self.inner.comment

    class AnyTransactionRent(AnyTransaction):
        def __init__(self, inner: RentPayment) -> None:
            super().__init__()
            self.inner = inner

        @property
        def date(self) -> date:
            return self.inner.received_on

        @property
        def type(self) -> str:
            return 'Rent payment'

        @property
        def amount(self) -> int:
            return self.inner.amount

        @property
        def comment(self) -> str:
            return f'For month {self.inner.for_month.strftime(month_format)}'

    all_transactions: list[AnyTransaction] = sorted(
        [typing.cast(AnyTransaction, AnyTransactionOtherTransaction(other_transaction))
         for other_transaction in data.rent_manager_main_state.other_transactions]
        +
        [AnyTransactionRent(rent_payment) for rent_payment in data.rent_manager_main_state.rent_payments]
        ,
        key=operator.attrgetter('date')
    )
    with pdf.tag('h1'):
        pdf.put('All transactions')

    any_transaction: AnyTransaction
    pdf.put_table(['Date', 'Type', 'Amount', ('Comment', 3)], [
        [
            any_transaction.date.strftime(date_format),
            any_transaction.type,
            format_currency(any_transaction.amount),
            any_transaction.comment + ' '
        ]
        for any_transaction in all_transactions
    ])

    pdf.output(str(export_path))


if __name__ == '__main__':
    hello_world()

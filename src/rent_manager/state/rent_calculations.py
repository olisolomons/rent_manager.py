import logging
from dataclasses import dataclass
from datetime import date

from rent_manager.state.all_transactions import get_all_transactions, AnyTransaction
from rent_manager.state.other_transaction import OtherTransaction, TransactionReason
from rent_manager.state.rent_manager_state import RentManagerState
from rent_manager.state.rent_payment import RentPayment


@dataclass
class BalanceAnnotatedTransaction:
    inner: AnyTransaction
    current_balance: int
    current_float: int


@dataclass(frozen=True)
class RentCalculations:
    rent_manager_state: RentManagerState
    rent_for_months: list[tuple[date, int]]
    unclaimed_commission: int
    total_rent_due: int
    total_rent_received: int
    other_transaction_sums: dict[TransactionReason, int]
    float_: int  # :)
    balance_annotated_transactions: list[BalanceAnnotatedTransaction]

    @classmethod
    def from_rent_manager_state(cls, rent_manager_state: RentManagerState):
        start_date = rent_manager_state.rent_arrangement_data.start_date
        months_since_start = date.today().month - start_date.month + 12 * (date.today().year - start_date.year)
        if date.today().day >= start_date.day:
            months_since_start += 1
        rent_for_months = {
            date(
                start_date.year + (start_date.month + month - 1) // 12,
                (start_date.month + month - 1) % 12 + 1,
                1
            ): 0
            for month in range(months_since_start)
        }

        for rent_payment in rent_manager_state.rent_manager_main_state.rent_payments:
            try:
                rent_for_months[rent_payment.for_month] += rent_payment.amount
            except KeyError:
                logging.warning(
                    f'{rent_payment.for_month} is not a month in the rental period {start_date} to {date.today()}'
                )

        total_rent_received = sum(
            rent_payment.amount
            for rent_payment in rent_manager_state.rent_manager_main_state.rent_payments
        )
        total_rent_due = months_since_start * rent_manager_state.rent_arrangement_data.monthly_rent
        total_commission_due = int(total_rent_received * rent_manager_state.rent_arrangement_data.agents_fee / 100)
        other_transaction_sums = {
            reason: sum(
                transaction.amount
                for transaction in rent_manager_state.rent_manager_main_state.other_transactions
                if transaction.reason is reason
            )
            for reason in TransactionReason
        }

        balance_annotated_transactions = []

        float_ = rent_manager_state.rent_arrangement_data.initial_float
        balance = rent_manager_state.rent_arrangement_data.initial_balance
        for wrapped_transaction in get_all_transactions(rent_manager_state):
            transaction: RentPayment | OtherTransaction = wrapped_transaction.unwrap()
            match transaction:
                case RentPayment(amount=amount):
                    balance += amount
                case OtherTransaction(reason=TransactionReason.FloatIncrease, amount=amount):
                    balance -= amount
                    float_ += amount
                case OtherTransaction(reason=TransactionReason.Cost, amount=amount):
                    surplus_float = float_ - rent_manager_state.rent_arrangement_data.base_float
                    if surplus_float > 0:
                        payable_out_of_float = min(amount, surplus_float)
                        float_ -= payable_out_of_float
                        amount -= payable_out_of_float

                    if balance > 0:
                        payable_out_of_balance = min(amount, balance)
                        balance -= payable_out_of_balance
                        amount -= payable_out_of_balance

                    if float_ > 0:
                        payable_out_of_float = min(amount, float_)
                        float_ -= payable_out_of_float
                        amount -= payable_out_of_float

                    balance -= amount
                case OtherTransaction(amount=amount):
                    balance -= amount
                case _:
                    logging.warning(f'Expected RentPayment or OtherTransaction, not {transaction}.')
            balance_annotated_transactions.append(BalanceAnnotatedTransaction(wrapped_transaction, balance, float_))

        return cls(
            rent_manager_state=rent_manager_state,
            rent_for_months=list(rent_for_months.items()),
            unclaimed_commission=total_commission_due - other_transaction_sums[TransactionReason.AgentFee],
            total_rent_due=total_rent_due,
            total_rent_received=total_rent_received,
            other_transaction_sums=other_transaction_sums,
            float_=float_,
            balance_annotated_transactions=balance_annotated_transactions
        )

    @property
    def arrears(self):
        return self.total_rent_due - self.total_rent_received

    @property
    def balance(self):
        arrangement = self.rent_manager_state.rent_arrangement_data
        return (arrangement.initial_balance + self.total_rent_received
                - (self.total_costs - self.other_transaction_sums[TransactionReason.FloatIncrease])
                - (self.float_ - arrangement.initial_float))

    @property
    def total_costs(self):
        return sum(self.other_transaction_sums.values())

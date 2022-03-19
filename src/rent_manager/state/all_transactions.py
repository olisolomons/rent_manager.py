import abc
import operator
import typing
from datetime import date

from .other_transaction import OtherTransaction
from .rent_manager_state import RentManagerState
from .rent_payment import RentPayment


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

    @abc.abstractmethod
    def unwrap(self):
        pass


class AnyTransactionOther(AnyTransaction):
    def __init__(self, inner: OtherTransaction) -> None:
        super().__init__()
        self.inner: OtherTransaction = inner

    @property
    def date(self) -> date:
        return self.inner.date_

    @property
    def type(self) -> str:
        return self.inner.reason.readable_name()

    @property
    def amount(self) -> int:
        return self.inner.amount

    @property
    def comment(self) -> str:
        return self.inner.comment

    def unwrap(self):
        return self.inner


class AnyTransactionRent(AnyTransaction):
    def __init__(self, inner: RentPayment) -> None:
        super().__init__()
        self.inner: RentPayment = inner

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
        month_format = '%b %Y'
        return f'For month {self.inner.for_month.strftime(month_format)}'

    def unwrap(self):
        return self.inner


def get_all_transactions(data: RentManagerState) -> list[AnyTransaction]:
    """
    Get both rent and other transactions in a unified list of `AnyTransaction`s
    :param data: The rent manager state
    :return: the combined list of all transactions
    """
    return sorted(
        [typing.cast(AnyTransaction, AnyTransactionRent(rent_payment)) for rent_payment in
         data.rent_manager_main_state.rent_payments]
        +
        [AnyTransactionOther(other_transaction)
         for other_transaction in data.rent_manager_main_state.other_transactions]
        ,
        key=operator.attrgetter('date')
    )

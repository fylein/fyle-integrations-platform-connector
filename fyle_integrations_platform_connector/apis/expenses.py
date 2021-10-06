from typing import List
from datetime import datetime

from dateutil import parser

from .base import Base


class Expenses(Base):
    """Class for Expenses APIs."""
    SOURCE_ACCOUNT_MAP = {
        'PERSONAL_CASH_ACCOUNT': 'PERSONAL',
        'PERSONAL_CORPORATE_CREDIT_CARD_ACCOUNT': 'CCC'
    }

    def get(self, query_params: dict=None, filter_negative_expenses: bool=False) -> List[dict]:
        """
        Get expenses.

        Args:
            query_params (dict): Query parameters.
            filter_negative_expenses (bool): Filter negative expenses.

        Returns:
            List[dict]: Response.
        """
        all_expenses = []
        generator = self.connection.list_all(query_params)
        for expense_list in generator:
            if filter_negative_expenses:
                expenses = self.__filter_credit_expenses(expense_list)
            else:
                expenses = expense_list['data']
            all_expenses.extend(expenses)

        return self.__construct_expenses_objects(all_expenses)


    @staticmethod
    def __filter_credit_expenses(expense_list: dict) -> List[dict]:
        """
        Filter negative expenses.

        Args:
            expenses (dict): Expenses.

        Returns:
            list: Expenses.
        """
        return list(filter(lambda expense: expense['amount'] > 0, expense_list['data']))


    def __construct_expenses_objects(self, expenses: List[dict]) -> List[dict]:
        """
        Construct expenses objects.

        Args:
            expense (List[dict]): Expenses.

        Returns:
            list: Expenses.
        """
        objects = []

        for expense in expenses:
            custom_properties = {}

            for custom_field in custom_fields:
                custom_properties[custom_field['name']] = custom_field['value']

            objects.append({
                # 'employee_email': expense['employee']['user']['email'], # TODO: platform blocker
                'category': expense['category']['name'],
                'sub_category': expense['category']['sub_category'],
                'project': expense['project']['name'] if expense['project'] else None,
                'expense_number': expense['seq_num'],
                'org_id': expense['org_id'],
                'claim_number': expense['report']['seq_num'] if expense['report'] else None,
                'amount': expense['amount'],
                'currency': expense['currency'],
                'foreign_amount': expense['foreign_amount'],
                'foreign_currency': expense['foreign_currency'],
                'settlement_id': expense['report']['settlement_id'] if expense['report'] else None,
                'reimbursable': expense['is_reimbursable'],
                'state': expense['state'],
                'vendor': expense['merchant'],
                'cost_center': expense['cost_center']['name'] if expense['cost_center'] else None,
                'purpose': expense['purpose'],
                'report_id': expense['report_id'],
                'file_ids': expense['file_ids'],
                'spent_at': self.__format_date(expense['spent_at']),
                'approved_at': self.__format_date(expense['report']['last_approved_at']) if expense['report'] else None,
                'expense_created_at': expense['created_at'],
                'expense_updated_at': expense['updated_at'],
                'fund_source': Expenses.SOURCE_ACCOUNT_MAP[expense['source_account']['type']],
                'verified_at': self.__format_date(expense['last_verified_at']),
                'custom_properties': custom_properties
            })

        return objects


    @staticmethod
    def __format_date(date_string) -> datetime:
        """
        Format date.

        Args:
            date_string (str): Date string.

        Returns:
            dateime: Formatted date.
        """
        if date_string:
            date_string = parser.parse(date_string)

        return date_string

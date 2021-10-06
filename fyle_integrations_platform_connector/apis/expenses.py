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

    def get(self, fund_source: List[str], import_state: str, last_synced_at: datetime=None,
        filter_negative_expenses: bool=False) -> List[dict]:
        """
        Get expenses.

        Args:
            fund_source (List[str]): Fund source.
            import_state (str): Import state.
            last_synced_at (datetime, optional): Last synced at. Defaults to None.
            filter_negative_expenses (bool, optional): Filter negative expenses. Defaults to False.
        
        Returns:
            List[dict]: Response.
        """
        all_expenses = []

        query_params = self.__construct_expenses_query_params(fund_source, import_state, last_synced_at)
        generator = self.connection.list_all(query_params)

        for expense_list in generator:
            if filter_negative_expenses:
                expenses = self.__filter_credit_expenses(expense_list)
            else:
                expenses = expense_list['data']
            all_expenses.extend(expenses)

        return self.__construct_expenses_objects(all_expenses)


    @staticmethod
    def __construct_expenses_query_params(fund_source: List[str], import_state: str, updated_at: datetime) -> dict:
        import_state = [import_state]
        if import_state[0] == 'PAYMENT_PROCESSING' and updated_at is not None:
            import_state.append('PAID')
            import_state = 'in.{}'.format(tuple(import_state)).replace("'", '"')
        else:
            import_state = 'eq.{}'.format(import_state[0])

        source_account_type = ['PERSONAL_CASH_ACCOUNT']
        if len(fund_source) == 1:
            source_account_type = 'eq.{}'.format(source_account_type[0])
        elif len(fund_source) > 1 and 'CCC' in fund_source:
            source_account_type.append('PERSONAL_CORPORATE_CREDIT_CARD_ACCOUNT')
            source_account_type = 'in.{}'.format(tuple(source_account_type)).replace("'", '"')

        if updated_at:
            updated_at = 'gte.{}'.format(datetime.strftime(updated_at, '%Y-%m-%dT%H:%M:%S.000Z'))

        query_params = {
            'order': 'updated_at.desc',
            'source_account->type': source_account_type,
            'state': import_state
        }

        if updated_at:
            query_params['updated_at'] = updated_at

        return query_params


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

            for custom_field in expense['custom_fields']:
                custom_properties[custom_field['name']] = custom_field['value']

            objects.append({
                'id': expense['id'],
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

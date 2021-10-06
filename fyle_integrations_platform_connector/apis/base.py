from datetime import datetime
from typing import List

# TODO: Add this import
# from fyle_accounting_mappings.models import ExpenseAttribute


class Base:
    """The base class for all API classes."""

    def __init__(self, attribute_type: str = None):
        self.attribute_type = attribute_type
        self.connection = None
        self.workspace_id = None


    def set_connection(self, connection):
        self.connection = connection


    def set_workspace_id(self, workspace_id):
        self.workspace_id = workspace_id


    @staticmethod
    def __format_date(last_synced_at: datetime) -> str:
        """
        Formats the date in the format of gte.2021-09-30T11:00:57.000Z
        """
        return 'gte.{}'.format(datetime.strftime(last_synced_at, '%Y-%m-%dT%H:%M:%S.000Z'))


    @staticmethod
    def __get_last_synced_at() -> datetime:
        """
        Returns the last time the API was synced.
        """
        # TODO: Add this
        # return ExpenseAttribute.get_last_synced_at(self.attribute_type)
        return None


    def construct_query_params(self) -> dict:
        """
        Constructs the query params for the API call.
        :return: dict
        """
        last_synced_at = self.__get_last_synced_at()
        updated_at = self.__format_date(last_synced_at) if last_synced_at else None

        # TODO: check is_enabled for all apis
        params = {'order': 'updated_at.desc', 'is_enabled': 'eq.true'}
        if updated_at:
            params['updated_at'] = updated_at

        return params


    def get_all_generator(self):
        """
        Returns the generator for retrieving data from the API.
        """
        query_params = self.construct_query_params()

        return self.connection.list_all(query_params)


    def bulk_create_or_update_expense_attributes(self, attributes: List[dict], update_existing: bool = False) -> None:
        """
        Bulk creates or updates expense attributes.
        :param attributes: List of expense attributes.
        :param update_existing: If True, updates/creates the existing expense attributes.
        """
        ExpenseAttribute.bulk_create_or_update_expense_attributes(
            attributes, self.attribute_type, self.workspace_id, update_existing
        )


    def __construct_expense_attribute_objects(self, generator) -> List[dict]:
        """
        Constructs the expense attribute objects.
        :param generator: Generator
        :return: List of expense attribute objects.
        """
        attributes = []
        for items in generator:
            attributes = []
            for row in items:
                attributes.append({
                    'attribute_type': self.attribute_type,
                    'display_name': 'Category', # TODO change this, check all apps
                    'value': row['name'],
                    'source_id': row['id']
                })

        return attributes


    def sync(self) -> None:
        """
        Syncs the latest API data to DB.
        """
        generator = self.get_all_generator()
        attributes = self.__construct_expense_attribute_objects(generator)
        self.bulk_create_or_update_expense_attributes(attributes)

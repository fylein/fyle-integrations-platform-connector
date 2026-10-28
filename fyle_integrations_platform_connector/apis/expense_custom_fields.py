from datetime import datetime, timezone
import logging
from .base import Base

logger = logging.getLogger(__name__)
logger.level = logging.INFO


class ExpenseCustomFields(Base):
    """Class for Expense Custom Fields APIs."""

    def sync(self, sync_after: datetime = None):
        """
        Syncs the latest API data to DB.
        :param sync_after: Sync after timestamp for incremental sync
        """
        try:
            query_params = {'order': 'updated_at.desc', 'is_custom': 'eq.true', 'type': 'eq.SELECT', 'is_enabled': 'eq.true'}
            
            # Add sync_after filter for incremental sync (webhook mode)
            if sync_after:
                updated_at = self.format_date(sync_after)
                query_params['updated_at'] = updated_at
            
            generator = self.connection.list_all(query_params)

            for items in generator:
                for row in items['data']:
                    if self.attribute_is_valid(row):
                        attributes = []
                        count = 1
                        attribute_type = row['field_name'].upper().replace(' ', '_')
                        for option in row['options']:
                            attributes.append({
                                'attribute_type': attribute_type,
                                'display_name': row['field_name'],
                                'value': option,
                                'active': True,
                                'source_id': 'expense_custom_field.{}.{}'.format(row['field_name'].lower(), count),
                                'detail': {
                                    'custom_field_id': row['id'],
                                    'placeholder': row['placeholder'],
                                    'is_mandatory': row['is_mandatory'],
                                    'is_dependent': False
                                }
                            })
                            count = count + 1
                        self.attribute_type = attribute_type
                        self.bulk_create_or_update_expense_attributes(attributes, True)

        except Exception as e:
            logger.exception(e)

    def list_all(self, query_params=None):
        """
        List all the custom fields
        """
        if not query_params:
            query_params = {'order': 'updated_at.desc', 'is_custom': 'eq.true', 'is_enabled': 'eq.true'}
        generator = self.connection.list_all(query_params)
        custom_fields = []

        for items in generator:
            custom_fields = items['data']

        return custom_fields

    def get_count(self, field_name: str) -> int:
        """
        Get count of attributes
        """
        query_params = {'order': 'updated_at.desc', 'limit': 1, 'offset': 0, 'is_enabled': 'eq.true', 'field_name': 'eq.{}'.format(field_name)}
        custom_field = self.connection.list_all(query_params)
        count = 0

        if custom_field:
            count = len(custom_field[0]['options'])

        return count

    def disable_all(self, custom_field_ids: list[int]) -> None:
        """
        Disable all the custom fields with the given IDs.
        :param custom_field_ids: List of custom field IDs to disable.
        """
        query_params = {
            'order': 'id.asc',
            'is_custom': 'eq.true',
            'is_enabled': 'eq.true',
            'id': 'in.({})'.format(','.join(map(str, custom_field_ids)))
        }
        generator = self.list_all(query_params=query_params)

        for row in generator:
            if self.attribute_is_valid(row):
                custom_field_name = row['field_name']
                custom_field_id = row['id']
                payload = {
                    'field_name': custom_field_name,
                    'type': 'SELECT',
                    'is_enabled': False,
                    'is_mandatory': False,
                    'options': [],
                    'id': custom_field_id
                }
                self.post(payload=payload)
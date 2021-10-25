# 'is_custom': 'eq.true',
#         'type': 'eq.SELECT',

from .base import Base


class ExpenseCustomFields(Base):
    """Class for Expense Fields APIs."""

    def sync(self):
        """
        Syncs the latest API data to DB.
        """
        query_params = {'order': 'updated_at.desc', 'is_custom': 'eq.true', 'type': 'eq.SELECT', 'is_enabled': 'eq.true'}
        generator = self.connection.list_all(query_params)

        for items in generator:
            attributes = []
            for row in items['data']:
                count = 1
                attribute_type = row['field_name'].upper().replace(' ', '_')
                for option in row['options']:
                    attributes.append({
                        'attribute_type': attribute_type,
                        'display_name': row['field_name'],
                        'value': option,
                        'source_id': 'expense_custom_field.{}.{}'.format(row['field_name'].lower(), count)
                    })
                    count = count + 1
                self.attribute_type = attribute_type
                self.bulk_create_or_update_expense_attributes(attributes, True)

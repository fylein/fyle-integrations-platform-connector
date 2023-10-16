from .base import Base


class DependentFields(Base):
    """
    Class For Expense Fields
    """

    def __init__(self):
        Base.__init__(self, attribute_type='EXPENSE_FIELDS')

    def get_project_field_id(self):
        """
        Get Project Field ID
        """
        query_params = {'limit': 1, 'order': 'updated_at.desc', 'offset': 0, 'field_name': 'eq.Project', 'is_custom': 'eq.False'}
        projects = self.connection.list(query_params)

        project_field_id = None

        if (len(projects['data'])) > 0:
            project_field_id = projects['data'][0]['id']

        return project_field_id


    def bulk_post_dependent_expense_field_values(self, data):
        """
        Post of Expense Field Values
        """
        payload = {
            'data': data
        }
        return self.connection.bulk_post_dependent_expense_field_values(payload)


    def sync(self):
        """
        Syncs the latest API data to DB.
        """
        generator = self.connection.list_all(query_params={'order': 'updated_at.desc', 'is_enabled': 'eq.true', 'is_custom': 'eq.true', 'type': 'eq.DEPENDENT_SELECT'})

        for items in generator:
            for row in items['data']:
                parent_field_id = row['parent_field_id']
                id = row['id']

                options = self.connection.get_dependent_expense_field_values(
                    expense_field_id=id, parent_expense_field_id=parent_field_id
                )

                attributes = []
                count = 1
                attribute_type = row['field_name'].upper().replace(' ', '_')

                for option in options['data']:
                    attributes.append({
                        'attribute_type': attribute_type,
                        'display_name': row['field_name'],
                        'value': option['expense_field_value'],
                        'active': True,
                        'source_id': 'expense_custom_field.{}.{}'.format(row['field_name'].lower(), count),
                        'detail': {
                            'custom_field_id': row['id'],
                            'placeholder': row['placeholder'],
                            'is_mandatory': row['is_mandatory']
                        }
                    })
                    count = count + 1

                self.attribute_type = attribute_type
                self.bulk_create_or_update_expense_attributes(attributes, True)
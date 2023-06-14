from .base import Base


class ExpenseFields(Base):
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


    def get_dependent_expense_field_values(self):
        """
        Get of Dependent Expense Field Values
        """

        return self.connection.get_dependent_expense_field_values()

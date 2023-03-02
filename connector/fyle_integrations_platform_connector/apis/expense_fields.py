from .base import Base


class ExpenseFields(Base):
    """
    Class For Expense Fields
    """

    def __init__(self):
        Base.__init__(self, attribute_type='EXPENSE_FIELDS')


    def sync(self):
        """
        Syncs the latest API data to DB.
        """
        query_params = {'limit': 1, 'order': 'updated_at.desc', 'offset': 0, 'field_name': 'in.(Project)', 'is_custom': 'eq.False'}
        projects = self.connection.list(query_params)

        self.create_or_update_expense_fields(projects['data'], ['Project'])

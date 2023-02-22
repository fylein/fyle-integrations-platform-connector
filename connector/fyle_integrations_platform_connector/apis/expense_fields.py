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
        generator = self.get_all_generator()
        for items in generator:
            for expense_field in items['data']:
                if expense_field['field_name'] in ['Project', 'Cost Center']:   
                    self.create_or_update_expense_fields(expense_field)

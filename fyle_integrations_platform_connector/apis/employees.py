from typing import List

from .base import Base


class Employees(Base):
    """Class for Employees APIs."""

    def __init__(self):
        Base.__init__(self, attribute_type='EMPLOYEE')

    def sync(self):
        """
        Syncs the latest API data to DB.
        """
        generator = self.get_all_generator()
        for items in generator:
            employee_attributes = []
            for employee in items:
                employee_attributes.append({
                    'attribute_type': 'EMPLOYEE',
                    'display_name': 'Employee',
                    'value': employee['user']['email'],
                    'source_id': employee['id'],
                    'detail': {
                        'employee_code': employee['code'],
                        'full_name': employee['user']['full_name'],
                        'location': employee['location'],
                        'department': employee['department'], # TODO: check this
                        'department_id': employee['department_id'],
                        'department_code': employee['department']['code']
                    }
                })

            self.bulk_create_or_update_expense_attributes(employee_attributes, True)


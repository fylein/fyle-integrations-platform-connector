from typing import List

from .base import Base


class Categories(Base):
    """Class for Categories APIs."""

    def __init__(self):
        Base.__init__(self, attribute_type='CATEGORY')


    def sync(self):
        """
        Syncs the latest API data to DB.
        """
        generator = self.get_all_generator()
        for items in generator:
            category_attributes = []
            for category in items['data']:
                if category['name'] != category['sub_category']:
                    category['name'] = '{0} / {1}'.format(category['name'], category['sub_category'])

                category_attributes.append({
                    'attribute_type': 'CATEGORY',
                    'display_name': 'Category',
                    'value': category['name'],
                    'source_id': category['id']
                })

            self.bulk_create_or_update_expense_attributes(category_attributes)

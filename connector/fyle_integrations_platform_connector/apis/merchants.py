from heapq import merge
from traceback import print_tb
from .base import Base
from typing import List

class Merchants(Base):
    """
    Class for Merchants API
    """
    def __init__(self):
        Base.__init__(self, attribute_type='MERCHANT', query_params={'field_name':'eq.Merchant'})

    def post(self, payload: List[str]):
        """
        Post data to Fyle 
        """
        generator = self.get_all_generator()
        for items in generator:
            merchant=items['data'][0]
            merchant['options'].extend(payload)
            merchant_payload = { 
                "id": merchant['id'],
                "field_name": "Merchant",
                "type": "SELECT",
                "options": merchant['options'],
                "placeholder": merchant['placeholder'],
                "category_ids": merchant['category_ids'],
                "is_enabled": merchant['is_enabled'],
                "is_custom": merchant['is_custom'],
                "is_mandatory": merchant['is_mandatory'],
                "code": merchant['code'],
                "default_value": merchant['default_value'],
            }

        return self.connection.post({'data': merchant_payload})

    def sync(self):
        """
        Syncs the latest API data to DB.
        """
        generator = self.get_all_generator()
        for items in generator:
            merchant=items['data'][0]
            merchant_attributes = []
            for option in merchant['options']:
                    merchant_attributes.append({
                        'attribute_type': 'MERCHANT',
                        'display_name': 'Merchant',
                        'value': option,
                        'source_id': merchant['id'],
                    })

            self.bulk_create_or_update_expense_attributes(merchant_attributes, True)


    

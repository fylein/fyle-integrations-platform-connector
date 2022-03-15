from heapq import merge
from traceback import print_tb

from apps.workspaces.models import Workspace
from .base import Base
from typing import List
from fyle_accounting_mappings.models import ExpenseAttribute

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
            workspace_id = Workspace.objects.filter(fyle_org_id=merchant['org_id']).values_list('id',flat=True)[0]
            existing_merchants = ExpenseAttribute.objects.filter(
                attribute_type='MERCHANT', workspace_id=workspace_id)
            delete_merchant_ids = []

            if(existing_merchants):
                for existing_merchant in existing_merchants:
                    if existing_merchant.value not in merchant['options']:
                        delete_merchant_ids.append(existing_merchant.id)
                    
                ExpenseAttribute.objects.filter(id__in = delete_merchant_ids).delete()

            merchant_attributes = []

            for option in merchant['options']:
                merchant_attributes.append({
                    'attribute_type': 'MERCHANT',
                    'display_name': 'Merchant',
                    'value': option,
                    'source_id': merchant['id'],
                })

            self.bulk_create_or_update_expense_attributes(merchant_attributes, True)


    

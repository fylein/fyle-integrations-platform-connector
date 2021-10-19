from .base import Base


class CorporateCards(Base):
    """Class for Corporate Cards APIs."""

    def __init__(self):
        Base.__init__(self, attribute_type='CORPORATE_CARD')

    def sync(self):
        """
        Syncs the latest API data to DB.
        """
        generator = self.get_all_generator()
        for items in generator:
            card_attributes = []
            for card in items['data']:
                card_attributes.append({
                    'attribute_type': self.attribute_type,
                    'display_name': self.attribute_type.replace('_', ' ').title(),
                    'value': card['card_number'],
                    'source_id': card['id'],
                    'detail': {
                        'bank_name': card['bank_name'],
                        'cardholder_name': card['cardholder_name']
                    }
                })

            self.bulk_create_or_update_expense_attributes(card_attributes, True)

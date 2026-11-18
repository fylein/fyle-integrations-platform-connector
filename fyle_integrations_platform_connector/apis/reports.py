from .base import Base

class Reports(Base):

    def bulk_mark_as_paid(self, data):

        payload = {
            'data': data
        }

        return self.connection.bulk_mark_as_paid(payload)

    def bulk_reset_accounting_export_summary(self, data):
        """
        Bulk reset accounting export summary for the given data.
        :params data: List of accounting export summary objects to reset.
        :returns: Response from the API.
        """
        return self.connection.bulk_reset_accounting_export_summary(data)

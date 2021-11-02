from connector.fyle_integrations_platform_connector import PlatformConnector
from apps.workspaces.models import FyleCredential

workspace_id = 1

fyle_credential = FyleCredential.objects.get(workspace_id=workspace_id)

connector = PlatformConnector(fyle_credential, workspace_id)


# Get Expenses
print(connector.expenses.get(
    source_account_type=['PERSONAL_CASH_ACCOUNT', 'PERSONAL_CORPORATE_CREDIT_CARD_ACCOUNT'], state='PAID', filter_credit_expenses=True
))

# Import Fyle Dimensions to sqlite db
connector.import_fyle_dimensions()

import os

from connector.fyle_integrations_platform_connector import PlatformConnector


connector = PlatformConnector(
    cluster_domain=os.environ['CLUSTER_DOMAIN'],
    token_url=os.environ['TOKEN_URL'],
    client_id=os.environ['CLIENT_ID'],
    client_secret=os.environ['CLIENT_SECRET'],
    refresh_token=os.environ['REFRESH_TOKEN'],
    workspace_id=1
)


# Get Expenses
print(connector.expenses.get(
    source_account_types=['PERSONAL_CASH_ACCOUNT', 'PERSONAL_CORPORATE_CREDIT_CARD_ACCOUNT'], import_state='PAID', filter_credit_expenses=True
))

# Import Fyle Dimensions to sqlite db
connector.import_fyle_dimension()

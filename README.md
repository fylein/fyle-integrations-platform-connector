# Fyle Integrations Platform Connector

## Installation and Usage

A common platform connector for all the Fyle Integrations to interact with Fyle's Platform APIs

`pip install fyle-integrations-platform-connector`

##### Usage

```
from fyle_integrations_platform_connector import PlatformConnector

connector = PlatformConnector(fyle_credential=fyle_credential)

# Get Expenses
expenses = connector.expenses.get(
    source_account_type=['PERSONAL_CASH_ACCOUNT', 'PERSONAL_CORPORATE_CREDIT_CARD_ACCOUNT'],
    state='PAID',
    last_synced_at='2021-08-22T00:00:000.000Z',
    filter_credit_expenses=True
)

# Import Fyle dimensions
connector.import_fyle_dimensions()

# Import specific Fyle dimensions
connector.employees.sync()
connector.projects.sync()
```

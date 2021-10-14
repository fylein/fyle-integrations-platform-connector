# Fyle Integrations Platform Connector

## Installation and Usage

A common platform connector for all the Fyle Integrations to interact with Fyle's Platform APIs

`pip install fyle_integrations_platform_connector`

##### In Django `settings.py`

    INSTALLED_APPS = [
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',
    
        # Installed Apps
        'rest_framework',
        'corsheaders',
        'fyle_rest_auth', # already existing reusable django app for authentication
        'fyle_accounting_mappings', # already existing mapping infra app,
        'fyle_integrations_platform_connector', # new platform connector
    
        # User Created Apps
        'apps.users',
        'apps.workspaces',
        'apps.mappings',
        'apps.fyle',
        'apps.quickbooks_online',
        'apps.tasks'
    ]


##### Usage

```
from fyle_integrations_platform_connector import PlatformConnector as PlatformIntegrationsConnector

connector = PlatformIntegrationsConnector(
    cluster_domain=cluster_domain,
    token_url=settings.FYLE_TOKEN_URI,
    client_id=settings.FYLE_CLIENT_ID, 
    client_secret=settings.FYLE_CLIENT_SECRET,
    refresh_token=refresh_token,
    workspace_id=workspace_id
)

# Get Expenses
expenses = connector.expenses.get(
    source_account_types=['PERSONAL_CASH_ACCOUNT', 'PERSONAL_CORPORATE_CREDIT_CARD_ACCOUNT'],
    import_state='PAID',
    last_synced_at='2021-08-22T00:00:000.000Z',
    filter_negative_expenses=True
)

# Import Fyle dimensions
connector.import_fyle_dimension()

# Import specific Fyle dimensions
connector.employees.sync()
connector.projects.sync()
```

## Local Development
### Setup

Setup virtual environment and install dependencies -
`virtualenv venv && pip install -r requirements.txt`

Copy sample secrets file and add secret environment variables -
`cp sample_secrets.sh secrets.sh`


##### Run a raw python script [(script.py)](https://github.com/fylein/fyle-integrations-platform-connector/blob/master/script.py)
```
bash run.sh
```

##### Bash into DB and check data
```
sqlite3 db.sqlite3

-- Example query
select attribute_type, count(*) from expense_attributes group by attribute_type;
```

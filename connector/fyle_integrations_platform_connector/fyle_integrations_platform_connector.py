import logging
import os

from fyle.platform import Platform

from apps.workspaces.models import FyleCredential
from .apis import Expenses, Employees, Categories, Projects, CostCenters, ExpenseCustomFields, CorporateCards

logger = logging.getLogger(__name__)
logger.level = logging.INFO


class PlatformConnector:
    """The main class creates a connection with Fyle Platform APIs using OAuth2 authentication
    (refresh token grant type).

    Parameters:
    fyle_credential (str): Fyle Credential instance.
    """

    def __init__(self, fyle_credentials: FyleCredential):
        server_url = '{}/platform/v1'.format(fyle_credentials.cluster_domain)
        self.workspace_id = fyle_credentials.workspace_id

        self.connection = Platform(
            server_url=server_url,
            token_url=os.environ.get('FYLE_TOKEN_URI'),
            client_id=os.environ.get('FYLE_CLIENT_ID'),
            client_secret=os.environ.get('FYLE_CLIENT_SECRET'),
            refresh_token=fyle_credentials.refresh_token
        )

        self.expenses = Expenses()
        self.employees = Employees()
        self.categories = Categories()
        self.projects = Projects()
        self.cost_centers = CostCenters()
        self.expense_custom_fields = ExpenseCustomFields()
        self.corporate_cards = CorporateCards()

        self.set_connection()
        self.set_workspace_id()


    def set_connection(self):
        """Set connection with Fyle Platform APIs."""
        self.expenses.set_connection(self.connection.v1.admin.expenses)
        self.employees.set_connection(self.connection.v1.admin.employees)
        self.categories.set_connection(self.connection.v1.admin.categories)
        self.projects.set_connection(self.connection.v1.admin.projects)
        self.cost_centers.set_connection(self.connection.v1.admin.cost_centers)
        self.expense_custom_fields.set_connection(self.connection.v1.admin.expense_fields)
        self.corporate_cards.set_connection(self.connection.v1.admin.corporate_cards)


    def set_workspace_id(self):
        """Set workspace ID for Fyle Platform APIs."""
        self.expenses.set_workspace_id(self.workspace_id)
        self.employees.set_workspace_id(self.workspace_id)
        self.categories.set_workspace_id(self.workspace_id)
        self.projects.set_workspace_id(self.workspace_id)
        self.cost_centers.set_workspace_id(self.workspace_id)
        self.expense_custom_fields.set_workspace_id(self.workspace_id)
        self.corporate_cards.set_workspace_id(self.workspace_id)


    def import_fyle_dimensions(self):
        """Import Fyle Platform dimension."""
        apis = ['employees', 'categories', 'projects', 'cost_centers', 'expense_custom_fields', 'corporate_cards']

        for api in apis:
            dimension = getattr(self, api)
            try:
                dimension.sync()
            except Exception as e:
                logger.exception(e)

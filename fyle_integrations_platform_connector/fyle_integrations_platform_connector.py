from fyle.platform import Platform

from .apis import Expenses, Employees, Categories


class FyleIntegrationsPlatformConnector:
    """The main class creates a connection with Fyle Platform APIs using OAuth2 authentication (refresh token grant type).

    Parameters:
    cluster_domain (str): Fyle Platform cluster domain.
    token_url (str): Fyle Platform token URL.
    client_id (str): Fyle Platform client ID.
    client_secret (str): Fyle Platform client secret.
    refresh_token (str): Fyle Platform refresh token.
    workspace_id (str): Fyle Platform workspace ID. (optional)
    """

    def __init__(self, cluster_domain: str, token_url: str, client_id: str, client_secret: str,
        refresh_token: str, workspace_id=None):
        server_url = '{}/platform/v1'.format(cluster_domain)
        self.workspace_id = workspace_id

        self.connection = Platform(
            server_url=server_url,
            token_url=token_url,
            client_id=client_id,
            client_secret=client_secret,
            refresh_token=refresh_token
        )

        self.expenses = Expenses()
        self.employees = Employees()
        self.categories = Categories()

        self.set_connection()
        self.set_workspace_id()


    def set_connection(self):
        """Set connection with Fyle Platform APIs."""
        self.expenses.set_connection(self.connection.v1.admin.expenses)
        self.employees.set_connection(self.connection.v1.admin.employees)
        self.categories.set_connection(self.connection.v1.admin.categories)


    def set_workspace_id(self):
        """Set workspace ID for Fyle Platform APIs."""
        self.expenses.set_workspace_id(self.workspace_id)
        self.employees.set_workspace_id(self.workspace_id)
        self.categories.set_workspace_id(self.workspace_id)


    def import_fyle_dimension(self):
        """Import Fyle Platform dimension."""
        apis = ['Employees, Categories']

        for api in apis:
            dimension = getattr(self, api)
            dimension.sync()

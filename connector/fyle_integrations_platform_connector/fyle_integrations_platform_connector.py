import logging
import os
from collections.abc import Iterator
from datetime import datetime

from fyle.platform import Platform
from fyle.platform.exceptions import ExpiredTokenError, InvalidTokenError

from apps.workspaces.models import FyleCredential, FeatureConfig
from fyle_accounting_mappings.models import FyleSyncTimestamp
from .token_manager import get_valid_access_token, save_access_token
from .apis import Expenses, Employees, Categories, Projects, CostCenters, ExpenseCustomFields, CorporateCards, \
    Reimbursements, TaxGroups, Merchants, Files, DependentFields, Departments, Subscriptions, Reports, CorporateCardTransactions, OrgSettings

logger = logging.getLogger(__name__)
logger.level = logging.INFO


RESOURCE_NAME_MAP = {
    'employees': 'employee',
    'categories': 'category',
    'projects': 'project',
    'cost_centers': 'cost_center',
    'expense_custom_fields': 'expense_field',
    'corporate_cards': 'corporate_card',
    'dependent_fields': 'dependent_field',
    'tax_groups': 'tax_group',
}


class PlatformConnectionProxy:
    """
    Wraps a low-level Fyle SDK resource connection and centralizes access-token fallback.

    The app code calls APIs through connector wrappers such as:
        platform.employees.connection.list(...)
        platform.expenses.connection.list_all(...)
        platform.reports.connection.bulk_mark_as_paid(...)

    Those underlying SDK calls can raise InvalidTokenError / ExpiredTokenError when the
    access token stored in FyleCredential looked valid locally but Fyle rejects it. The
    app folders should not need to know about this fallback path, and the SDK itself
    should not persist database state. This proxy sits between both layers:

    - SDK resource methods still make the actual Platform API calls.
    - PlatformConnector.refresh_access_token() asks Platform/Auth to call the token API.
    - PlatformConnector then saves the returned token and expiry in FyleCredential.
    - The original SDK method is retried once with the fresh access token.
    """

    def __init__(self, connection, refresh_access_token):
        self.connection = connection
        self.refresh_access_token = refresh_access_token

    def __getattr__(self, item):
        """
        Forward unknown attributes to the wrapped SDK resource connection.

        This lets the proxy behave like the original SDK resource without manually
        re-defining every method such as list, list_all, post, post_bulk, get_by_id,
        bulk_mark_as_paid, etc. Callable attributes are wrapped so token errors can be
        handled in one place.

        Some library code reaches one level deeper and calls the SDK ApiBase directly,
        for example:
            platform.org_settings.connection.api.make_post_request(...)

        In that case `api` is a non-callable object, but its methods still make Fyle
        HTTP calls and can raise token errors. Wrap nested SDK helper objects too, so
        those direct `.api.make_*_request(...)` paths get the same refresh fallback.
        """
        attribute = getattr(self.connection, item)
        if not callable(attribute):
            if self.__should_wrap_nested_attribute(attribute):
                return PlatformConnectionProxy(attribute, self.refresh_access_token)
            return attribute

        def wrapped(*args, **kwargs):
            # Delay method execution until __execute so both normal return values and
            # token failures go through the same refresh-and-retry path.
            return self.__execute(lambda: attribute(*args, **kwargs))

        return wrapped

    @staticmethod
    def __should_wrap_nested_attribute(attribute):
        """
        Return True for SDK helper objects that expose callable API methods.

        Avoid wrapping primitive values, dictionaries, lists, and other plain data. The
        intent is specifically to catch SDK objects such as ApiBase returned by `.api`.
        """
        if isinstance(attribute, (str, int, float, bool, dict, list, tuple, set, type(None))):
            return False

        return any(callable(getattr(attribute, name)) for name in dir(attribute))

    def __execute(self, operation):
        """
        Execute one SDK method and retry once if Fyle rejects the access token.

        A local access token can be within our 30-minute expiry window and still be
        invalid from Fyle's perspective. When that happens, refresh_access_token()
        calls Platform.update_access_token(), which keeps the external token API call
        inside Platform/Auth, and then persists the returned token in FyleCredential.
        """
        try:
            result = operation()
        except (InvalidTokenError, ExpiredTokenError):
            # Retry once after refreshing. If the retry still says the token is expired,
            # normalize it to InvalidTokenError so app folders do not need a new
            # ExpiredTokenError handling branch.
            self.refresh_access_token()
            try:
                result = operation()
            except ExpiredTokenError as exception:
                raise InvalidTokenError('Invalid refresh token') from exception

        if isinstance(result, Iterator):
            # list_all returns a generator. Its HTTP calls happen during iteration, not
            # when list_all() is first called, so token errors must be handled while the
            # caller consumes the generator.
            return self.__wrap_generator(result, operation)

        return result

    def __wrap_generator(self, generator, operation):
        """
        Iterate over SDK generators with the same one-time token refresh fallback.

        For generator-based SDK methods, an InvalidTokenError / ExpiredTokenError may
        be raised after some iteration has already started. On the first token failure,
        the proxy refreshes the token and recreates the generator by re-running the
        original operation. If Fyle rejects the refreshed token too, the error is
        surfaced as InvalidTokenError to preserve existing app-level behavior.
        """
        refreshed = False
        while True:
            try:
                yield next(generator)
            except StopIteration:
                return
            except (InvalidTokenError, ExpiredTokenError):
                if refreshed:
                    raise InvalidTokenError('Invalid refresh token')
                refreshed = True
                self.refresh_access_token()
                generator = operation()


def get_resource_timestamp(fyle_sync_timestamp: FyleSyncTimestamp, resource_name: str) -> datetime:
    """
    Get timestamp for a particular resource from FyleSyncTimestamp
    :param fyle_sync_timestamp: FyleSyncTimestamp object
    :param resource_name: Resource name (e.g., 'employees', 'categories', etc.)
    :return: timestamp or None
    """
    return getattr(fyle_sync_timestamp, f'{resource_name}_synced_at', None)


class PlatformConnector:
    """The main class creates a connection with Fyle Platform APIs using OAuth2 authentication
    (refresh token grant type).

    Parameters:
    fyle_credential (str): Fyle Credential instance.
    """

    def __init__(self, fyle_credentials: FyleCredential):
        server_url = '{}/platform/v1'.format(fyle_credentials.cluster_domain)
        self.fyle_credentials = fyle_credentials
        self.workspace_id = fyle_credentials.workspace_id
        try:
            access_token = get_valid_access_token(fyle_credentials)
            self.connection = Platform(
                server_url=server_url,
                token_url=os.environ.get('FYLE_TOKEN_URI'),
                client_id=os.environ.get('FYLE_CLIENT_ID'),
                client_secret=os.environ.get('FYLE_CLIENT_SECRET'),
                refresh_token=fyle_credentials.refresh_token,
                access_token=access_token
            )
            if not access_token:
                save_access_token(fyle_credentials, self.connection.get_access_token())
            
        except Exception as e:
            logger.exception('Unable to initialize Fyle Platform connection for workspace_id %s with exception %s', self.workspace_id, str(e))
            raise InvalidTokenError('Invalid refresh token')

        self.corporate_card_transactions = CorporateCardTransactions()
        self.expenses = Expenses()
        self.employees = Employees()
        self.categories = Categories()
        self.projects = Projects()
        self.cost_centers = CostCenters()
        self.expense_custom_fields = ExpenseCustomFields()
        self.corporate_cards = CorporateCards()
        self.reimbursements = Reimbursements()
        self.tax_groups = TaxGroups()
        self.merchants = Merchants()
        self.files = Files()
        self.departments = Departments()
        self.dependent_fields = DependentFields()
        self.subscriptions = Subscriptions()
        self.reports = Reports()
        self.org_settings = OrgSettings()
        self.set_connection()
        self.set_workspace_id()

    def refresh_access_token(self):
        logger.info(
            'Refreshing Fyle access token after invalid token response for workspace_id %s',
            self.workspace_id
        )
        access_token = self.connection.update_access_token()
        save_access_token(self.fyle_credentials, access_token)

    def set_connection(self):
        """Set connection with Fyle Platform APIs."""
        self.corporate_card_transactions.set_connection(
            PlatformConnectionProxy(
                self.connection.v1.admin.corporate_card_transactions,
                self.refresh_access_token
            )
        )
        self.expenses.set_connection(
            PlatformConnectionProxy(self.connection.v1.admin.expenses, self.refresh_access_token)
        )
        self.expenses.corporate_card_transactions = self.corporate_card_transactions
        self.employees.set_connection(
            PlatformConnectionProxy(self.connection.v1.admin.employees, self.refresh_access_token)
        )
        self.categories.set_connection(
            PlatformConnectionProxy(self.connection.v1.admin.categories, self.refresh_access_token)
        )
        self.projects.set_connection(
            PlatformConnectionProxy(self.connection.v1.admin.projects, self.refresh_access_token)
        )
        self.cost_centers.set_connection(
            PlatformConnectionProxy(self.connection.v1.admin.cost_centers, self.refresh_access_token)
        )
        self.expense_custom_fields.set_connection(
            PlatformConnectionProxy(self.connection.v1.admin.expense_fields, self.refresh_access_token)
        )
        self.corporate_cards.set_connection(
            PlatformConnectionProxy(self.connection.v1.admin.corporate_cards, self.refresh_access_token)
        )
        self.reimbursements.set_connection(
            PlatformConnectionProxy(self.connection.v1.admin.reimbursements, self.refresh_access_token)
        )
        self.tax_groups.set_connection(
            PlatformConnectionProxy(self.connection.v1.admin.tax_groups, self.refresh_access_token)
        )
        self.merchants.set_connection(
            PlatformConnectionProxy(self.connection.v1.admin.expense_fields, self.refresh_access_token)
        )
        self.files.set_connection(
            PlatformConnectionProxy(self.connection.v1.admin.files, self.refresh_access_token)
        )
        self.departments.set_connection(
            PlatformConnectionProxy(self.connection.v1.admin.departments, self.refresh_access_token)
        )
        self.dependent_fields.set_connection(
            PlatformConnectionProxy(
                self.connection.v1.admin.dependent_expense_field_values,
                self.refresh_access_token
            ),
            PlatformConnectionProxy(self.connection.v1.admin.expense_fields, self.refresh_access_token)
        )
        self.subscriptions.set_connection(
            PlatformConnectionProxy(self.connection.v1.admin.subscriptions, self.refresh_access_token)
        )
        self.reports.set_connection(
            PlatformConnectionProxy(self.connection.v1.admin.reports, self.refresh_access_token)
        )
        self.org_settings.set_connection(
            PlatformConnectionProxy(self.connection.v1.admin.org_settings, self.refresh_access_token)
        )

    def set_workspace_id(self):
        """Set workspace ID for Fyle Platform APIs."""
        self.corporate_card_transactions.set_workspace_id(self.workspace_id)
        self.expenses.set_workspace_id(self.workspace_id)
        self.employees.set_workspace_id(self.workspace_id)
        self.categories.set_workspace_id(self.workspace_id)
        self.projects.set_workspace_id(self.workspace_id)
        self.cost_centers.set_workspace_id(self.workspace_id)
        self.expense_custom_fields.set_workspace_id(self.workspace_id)
        self.corporate_cards.set_workspace_id(self.workspace_id)
        self.reimbursements.set_workspace_id(self.workspace_id)
        self.tax_groups.set_workspace_id(self.workspace_id)
        self.merchants.set_workspace_id(self.workspace_id)
        self.files.set_workspace_id(self.workspace_id)
        self.departments.set_workspace_id(self.workspace_id)
        self.dependent_fields.set_workspace_id(self.workspace_id)
        self.reports.set_workspace_id(self.workspace_id)
        self.org_settings.set_workspace_id(self.workspace_id)

    def import_fyle_dimensions(self, import_taxes: bool = False, import_dependent_fields: bool = False, is_export: bool = False, skip_dependent_field_ids: list = []):
        """Import Fyle Platform dimension."""
        apis = ['employees', 'categories', 'projects', 'cost_centers', 'expense_custom_fields', 'corporate_cards']
        fyle_sync_timestamp = None

        if is_export:
            apis = ['employees', 'cost_centers', 'expense_custom_fields', 'corporate_cards']

        if import_dependent_fields:
            apis.append('dependent_fields')

        if import_taxes:
            apis.append('tax_groups')

        fyle_webhook_sync_enabled = FeatureConfig.get_feature_config(workspace_id=self.workspace_id, key='fyle_webhook_sync_enabled')
        if fyle_webhook_sync_enabled:
            fyle_sync_timestamp = FyleSyncTimestamp.objects.get(workspace_id=self.workspace_id)

        for api in apis:
            dimension = getattr(self, api)
            try:
                if api == 'dependent_fields':
                    dimension.sync(skip_dependent_field_ids)
                else:
                    sync_after = None
                    resource_name = RESOURCE_NAME_MAP.get(api, api)
                    if fyle_webhook_sync_enabled and fyle_sync_timestamp:
                        sync_after = get_resource_timestamp(fyle_sync_timestamp, resource_name)
                        logger.debug(f'Syncing {api} for workspace_id {self.workspace_id} with webhook mode | sync_after: {sync_after}')
                    else:
                        logger.debug(f'Syncing {api} for workspace_id {self.workspace_id} with full sync mode')
                    dimension.sync(sync_after=sync_after)

                    if fyle_webhook_sync_enabled and fyle_sync_timestamp:
                        fyle_sync_timestamp.update_sync_timestamp(self.workspace_id, resource_name)
            except Exception as e:
                logger.exception(f'Error syncing {api} for workspace_id {self.workspace_id}: {e}')

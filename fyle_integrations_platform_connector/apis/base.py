import logging
from datetime import datetime
from typing import Dict, List

from apps.workspaces.models import Workspace

from fyle_accounting_mappings.models import ExpenseAttribute

logger = logging.getLogger(__name__)
logger.level = logging.INFO


class Base:
    """The base class for all API classes."""

    def __init__(self, attribute_type: str = None, query_params: dict = {}):
        self.attribute_type = attribute_type
        self.query_params = query_params
        self.connection = None
        self.workspace_id = None
        self.workspace = None

    def set_connection(self, connection):
        self.connection = connection

    def set_workspace_id(self, workspace_id):
        self.workspace_id = workspace_id
        self.workspace = Workspace.objects.filter(id=self.workspace_id).first()

    def format_date(self, last_synced_at: datetime) -> str:
        """
        Formats the date in the format of gte.2021-09-30T11:00:57.000Z
        """
        return 'gte.{}'.format(datetime.strftime(last_synced_at, '%Y-%m-%dT%H:%M:%S.000Z'))

    def __get_last_synced_at(self):
        """
        Returns the last time the API was synced.
        """
        return ExpenseAttribute.get_last_synced_at(self.attribute_type, self.workspace_id)

    def construct_query_params(self, sync_after: datetime = None) -> dict:
        """
        Constructs the query params for the API call.
        :param sync_after: Sync after timestamp for incremental sync (webhook mode)
        :return: dict
        """
        params = {'order': 'updated_at.desc'}
        params.update(self.query_params)

        if sync_after:
            updated_at = self.format_date(sync_after)
            params['updated_at'] = updated_at
            return params

        if self.attribute_type not in ('CATEGORY', 'PROJECT', 'COST_CENTER', 'EMPLOYEE', 'CORPORATE_CARD', 'MERCHANT'):
            last_synced_record = self.__get_last_synced_at()
            if last_synced_record:
                updated_at = self.format_date(last_synced_record.updated_at)
                params['updated_at'] = updated_at

        return params

    def get_all_generator(self, sync_after: datetime = None, params: dict = {}):
        """
        Returns the generator for retrieving data from the API.
        :param sync_after: Sync after timestamp for incremental sync (webhook mode)
        :param params: Additional query parameters to include in the API call.
        :return: Generator
        """
        query_params = self.construct_query_params(sync_after)
        query_params.update(params)

        return self.connection.list_all(query_params)

    def get_count(self):
        """
        Get count of attributes
        """
        params = {'order': 'updated_at.desc', 'limit': 1, 'offset': 0, 'is_enabled': 'eq.true'}
        return self.connection.list(params)['count']

    def post_bulk(self, payload: List[Dict]):
        """
        Post data to Fyle in Bulk
        """
        logger.info("Posting bulk payload for workspace_id: %s with: %s", self.workspace_id, payload)
        return self.connection.post_bulk({'data': payload})

    def post(self, payload: Dict):
        """
        Post date to Fyle
        """
        logger.info("Posting payload for workspace_id: %s with: %s", self.workspace_id, payload)
        return self.connection.post({'data': payload})

    def bulk_create_or_update_expense_attributes(self, attributes: List[dict], update_existing: bool = False) -> None:
        """
        Bulk creates or updates expense attributes.
        :param attributes: List of expense attributes.
        :param update_existing: If True, updates/creates the existing expense attributes.
        """
        ExpenseAttribute.bulk_create_or_update_expense_attributes(
            attributes, self.attribute_type, self.workspace_id, update_existing
        )

    def __construct_expense_attribute_objects(self, generator) -> List[dict]:
        """
        Constructs the expense attribute objects.
        :param generator: Generator
        :return: List of expense attribute objects.
        """
        attributes = []
        for items in generator:
            for row in items['data']:
                if self.attribute_is_valid(row):
                    attributes.append({
                        'attribute_type': self.attribute_type,
                        'display_name': self.attribute_type.replace('_', ' ').title(),
                        'value': row['name'],
                        'active': True,
                        'source_id': row['id']
                    })

        return attributes

    def attribute_is_valid(self, attribute):
        """
        Validate whether attribute is from the same org or not.
        """
        if hasattr(self.workspace, 'fyle_org_id'):
            return attribute['org_id'] == self.workspace.fyle_org_id

        elif hasattr(self.workspace, 'org_id'):
            return attribute['org_id'] == self.workspace.org_id

    def sync(self, sync_after: datetime = None) -> None:
        """
        Syncs the latest API data to DB.
        :param sync_after: Sync after timestamp for incremental sync
        """
        generator = self.get_all_generator(sync_after)
        attributes = self.__construct_expense_attribute_objects(generator)
        self.bulk_create_or_update_expense_attributes(attributes)

    def get_by_id(self, id):
        """
        Get Single Resource object by ID
        :param id: Resource object ID
        :return: Resource Object
        """
        return self.connection.get_by_id(id)['data']

    def delete_bulk(self, payload: dict):
        """
        Deletes multiple resources in bulk.
        :param payload: Payload containing the list of resource IDs to delete
        """
        if self.attribute_type in ('CATEGORY', 'PROJECT', 'COST_CENTER'):
            return self.connection.delete_bulk(data=payload)
        else:
            raise NotImplementedError('Bulk delete is not supported for this attribute type.')

    def delete_summary_bulk(self, payload: dict):
        """
        Deletes multiple resource summaries in bulk.
        :param payload: Payload containing the list of resource summary IDs to delete
        """
        if self.attribute_type in ('CATEGORY', 'PROJECT', 'COST_CENTER'):
            return self.connection.delete_summary_bulk(data=payload)
        else:
            raise NotImplementedError('Bulk delete is not supported for this attribute type.')

    def delete_or_disable(self, ids: list[int]):
        """
        Delete or disable resources by their IDs.
        :param ids: List of resource IDs to delete or disable.
        """
        if self.attribute_type not in ('CATEGORY', 'PROJECT', 'COST_CENTER'):
            raise NotImplementedError('Delete or disable is not supported for this attribute type.')
    
        data = []
        query_params = {
            'order': 'id.asc',
            'is_enabled': 'eq.true',
            'id': 'in.({})'.format(','.join(map(str, ids)))
        }

        resource_map = {
            'CATEGORY': 'categories',
            'PROJECT': 'projects',
            'COST_CENTER': 'cost_centers'
        }

        generator = self.connection.list_all(query_params=query_params)

        for items in generator:
            for resource in items['data']:
                if self.attribute_is_valid(resource):
                    data.append({
                        'id': resource['id'],
                        'name': resource['name'],
                        'is_enabled': False
                    })

        valid_resource_ids = [resource['id'] for resource in data]

        if not valid_resource_ids:
            return

        delete_summary_payload = [{'id': resource_id} for resource_id in valid_resource_ids]
        delete_summary = self.delete_summary_bulk(payload={"data": delete_summary_payload})

        resources_to_delete = delete_summary['data'][resource_map[self.attribute_type]]

        if resources_to_delete:
            self.delete_bulk(payload={"data": resources_to_delete})

        deleted_resource_ids = [resource['id'] for resource in resources_to_delete]
        resources_to_disable = []
        for resource in data:
            if resource['id'] not in deleted_resource_ids:
                resources_to_disable.append(resource)

        if resources_to_disable:
            self.post_bulk(payload=resources_to_disable)
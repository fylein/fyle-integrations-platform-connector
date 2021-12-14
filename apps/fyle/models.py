from typing import List, Dict

from django.db import models

from apps.workspaces.models import Workspace


class Reimbursement(models.Model):
    """
    Reimbursements
    """
    id = models.AutoField(primary_key=True)
    workspace = models.ForeignKey(
        Workspace, on_delete=models.PROTECT, help_text='To which workspace this reimbursement belongs to'
    )
    settlement_id = models.CharField(max_length=255, help_text='Fyle Settlement ID')
    reimbursement_id = models.CharField(max_length=255, help_text='Fyle Reimbursement ID')
    state = models.CharField(max_length=255, help_text='Fyle Reimbursement State')
    created_at = models.DateTimeField(auto_now_add=True, help_text='Created at')
    updated_at = models.DateTimeField(auto_now=True, help_text='Updated at')

    class Meta:
        db_table = 'reimbursements'


    @staticmethod
    def create_or_update_reimbursement_objects(reimbursements: List[Dict], workspace_id):
        """
        Create or Update reimbursement attributes
        """
        reimbursement_id_list = [reimbursement['id'] for reimbursement in reimbursements]
        existing_reimbursements = Reimbursement.objects.filter(
            reimbursement_id__in=reimbursement_id_list, workspace_id=workspace_id).all()

        existing_reimbursement_ids = []
        primary_key_map = {}

        for existing_reimbursement in existing_reimbursements:
            existing_reimbursement_ids.append(existing_reimbursement.reimbursement_id)
            primary_key_map[existing_reimbursement.reimbursement_id] = {
                'id': existing_reimbursement.id,
                'state': existing_reimbursement.state
            }

        attributes_to_be_created = []
        attributes_to_be_updated = []

        for reimbursement in reimbursements:
            reimbursement['state'] = 'COMPLETE' if reimbursement['is_paid'] else 'PENDING'
            if reimbursement['id'] not in existing_reimbursement_ids:
                attributes_to_be_created.append(
                    Reimbursement(
                        settlement_id=reimbursement['settlement_id'],
                        reimbursement_id=reimbursement['id'],
                        state=reimbursement['state'],
                        workspace_id=workspace_id
                    )
                )
            else:
                if reimbursement['state'] != primary_key_map[reimbursement['id']]['state']:
                    attributes_to_be_updated.append(
                        Reimbursement(
                            id=primary_key_map[reimbursement['id']]['id'],
                            state=reimbursement['state']
                        )
                    )

        if attributes_to_be_created:
            Reimbursement.objects.bulk_create(attributes_to_be_created, batch_size=50)

        if attributes_to_be_updated:
            Reimbursement.objects.bulk_update(attributes_to_be_updated, fields=['state'], batch_size=50)


    @staticmethod
    def get_last_synced_at(workspace_id: int):
        """
        Get last synced at datetime
        :param workspace_id: Workspace Id
        :return: last_synced_at datetime
        """
        return Reimbursement.objects.filter(
            workspace_id=workspace_id
        ).order_by('-updated_at').first()

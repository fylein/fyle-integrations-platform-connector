from django.db import models

# Create your models here.
class Workspace(models.Model):
    """
    Workspace model
    """
    id = models.AutoField(primary_key=True, help_text='Unique Id to identify a workspace')
    name = models.CharField(max_length=255, help_text='Name of the workspace')
    fyle_org_id = models.CharField(max_length=255, help_text='org id', unique=True)
    last_synced_at = models.DateTimeField(help_text='Datetime when expenses were pulled last', null=True)
    source_synced_at = models.DateTimeField(help_text='Datetime when source dimensions were pulled', null=True)
    destination_synced_at = models.DateTimeField(
        help_text='Datetime when destination dimensions were pulled', null=True)
    created_at = models.DateTimeField(auto_now_add=True, help_text='Created at datetime')
    updated_at = models.DateTimeField(auto_now=True, help_text='Updated at datetime')

    class Meta:
        db_table = 'workspaces'


class FyleCredential(models.Model):
    """
    Table to store Fyle credentials
    """
    id = models.AutoField(primary_key=True)
    refresh_token = models.TextField(help_text='Stores Fyle refresh token')
    cluster_domain = models.CharField(max_length=255, help_text='Cluster domain', null=True)
    workspace = models.OneToOneField(Workspace, on_delete=models.PROTECT, help_text='Reference to Workspace model')
    created_at = models.DateTimeField(auto_now_add=True, help_text='Created at datetime')
    updated_at = models.DateTimeField(auto_now=True, help_text='Updated at datetime')

    class Meta:
        db_table = 'fyle_credentials'

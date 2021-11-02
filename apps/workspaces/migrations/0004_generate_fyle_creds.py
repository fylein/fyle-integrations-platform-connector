import os

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('workspaces', '0003_fylecredential'),
    ]

    query = "insert into fyle_credentials (refresh_token, cluster_domain, workspace_id, created_at, updated_at) values ('{}', 'https://staging.fyle.tech', 1, date('now'), date('now'))".format(os.environ.get('REFRESH_TOKEN'))

    operations = [
        migrations.RunSQL(query)
    ]

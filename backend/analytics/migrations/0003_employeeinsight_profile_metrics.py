from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analytics', '0002_meetinganalysis'),
    ]

    operations = [
        migrations.AddField(
            model_name='employeeinsight',
            name='profile_metrics',
            field=models.JSONField(blank=True, default=dict),
        ),
    ]

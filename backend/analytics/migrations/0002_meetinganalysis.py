from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('meetings', '0001_initial'),
        ('analytics', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MeetingAnalysis',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transcript', models.TextField()),
                ('summary', models.TextField(blank=True, default='')),
                ('employee_sentiment_scores', models.JSONField(blank=True, default=dict)),
                ('participation_score', models.FloatField(default=0.0)),
                ('collaboration_signals', models.JSONField(blank=True, default=dict)),
                ('engagement_signals', models.JSONField(blank=True, default=dict)),
                ('conflict_detection', models.JSONField(blank=True, default=dict)),
                ('speaker_mapping', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('meeting', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='analysis', to='meetings.meeting')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]

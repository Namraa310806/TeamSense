from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Organization',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('organization_id', models.UUIDField(default=__import__('uuid').uuid4, editable=False, unique=True)),
                ('organization_name', models.CharField(max_length=255)),
                ('industry', models.CharField(blank=True, default='', max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='created_organizations',
                    to='auth.user',
                )),
            ],
            options={
                'ordering': ['organization_name'],
            },
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(
                    choices=[
                        ('ADMIN', 'Admin'),
                        ('EXECUTIVE', 'Executive'),
                        ('HR', 'HR'),
                        ('CHR', 'CHR'),
                    ],
                    default='HR',
                    max_length=20,
                )),
                ('designation', models.CharField(blank=True, default='', max_length=255)),
                ('department', models.CharField(blank=True, default='', max_length=255)),
                ('organization', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='members',
                    to='accounts.organization',
                )),
                ('user', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='profile',
                    to='auth.user',
                )),
            ],
        ),
    ]

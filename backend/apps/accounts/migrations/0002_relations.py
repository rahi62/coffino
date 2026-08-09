from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0001_initial'),
        ('auth', '0012_alter_user_first_name_max_length'),
        ('businesses', '0001_initial'),
    ]
    operations = [
        migrations.AddField(model_name='user', name='groups', field=models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
        migrations.AddField(model_name='user', name='user_permissions', field=models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
        migrations.AddField(model_name='user', name='business', field=models.ForeignKey('businesses.business', null=True, blank=True, on_delete=models.PROTECT, related_name='users')),
        migrations.AddField(model_name='user', name='branch', field=models.ForeignKey('businesses.branch', null=True, blank=True, on_delete=models.PROTECT, related_name='users')),
        migrations.AddField(model_name='manageroverridecredential', name='user', field=models.OneToOneField('accounts.user', on_delete=models.CASCADE, related_name='manager_override')),
    ]

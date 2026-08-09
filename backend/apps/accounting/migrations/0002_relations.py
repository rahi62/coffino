from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [
        ('accounting', '0001_initial'),
        ('accounts', '0001_initial'),
        ('businesses', '0001_initial'),
    ]
    operations = [
        migrations.AddField(model_name='expensecategory', name='branch', field=models.ForeignKey('businesses.branch', on_delete=models.CASCADE, related_name='expense_categories')),
        migrations.AddField(model_name='expense', name='branch', field=models.ForeignKey('businesses.branch', on_delete=models.CASCADE, related_name='expenses')),
        migrations.AddField(model_name='expense', name='category', field=models.ForeignKey('accounting.expensecategory', null=True, blank=True, on_delete=models.SET_NULL, related_name='expenses')),
        migrations.AddField(model_name='expense', name='created_by', field=models.ForeignKey('accounts.user', null=True, blank=True, on_delete=models.SET_NULL)),
        migrations.AddField(model_name='fixedoverhead', name='branch', field=models.ForeignKey('businesses.branch', on_delete=models.CASCADE, related_name='fixed_overheads')),
        migrations.AddField(model_name='fiscalsettings', name='branch', field=models.OneToOneField('businesses.branch', on_delete=models.CASCADE, related_name='fiscal_settings')),
    ]

import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('accounting', '0003_constraints'),
        ('businesses', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='BankAccount',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(max_length=120)),
                ('kind', models.CharField(choices=[('CARD', 'کارت بانکی'), ('ACCOUNT', 'حساب بانکی'), ('IBAN', 'شبای بانکی')], default='CARD', max_length=16)),
                ('bank_name', models.CharField(blank=True, max_length=120)),
                ('holder_name', models.CharField(blank=True, max_length=120)),
                ('identifier_last4', models.CharField(blank=True, max_length=4)),
                ('is_active', models.BooleanField(default=True)),
                ('branch', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='bank_accounts', to='businesses.branch')),
            ],
            options={'ordering': ['title', 'id']},
        ),
        migrations.AddConstraint(
            model_name='bankaccount',
            constraint=models.UniqueConstraint(fields=('branch', 'title'), name='unique_bank_account_title_per_branch'),
        ),
    ]

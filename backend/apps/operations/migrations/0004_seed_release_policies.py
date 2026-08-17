from django.db import migrations


def seed_release_policies(apps,schema_editor):
    ReleasePolicy=apps.get_model('operations','ReleasePolicy')
    for channel in ('stable','beta'):
        ReleasePolicy.objects.get_or_create(channel=channel)


def unseed_release_policies(apps,schema_editor):
    ReleasePolicy=apps.get_model('operations','ReleasePolicy')
    ReleasePolicy.objects.filter(
        channel__in=['stable','beta'],
        target_version='',minimum_version='',rollback_version='',rollout_percent=100,
        paused=False,blocked_versions=[],advisory_message='',required_after__isnull=True,
    ).delete()


class Migration(migrations.Migration):
    dependencies=[('operations','0003_constraints')]
    operations=[migrations.RunPython(seed_release_policies,unseed_release_policies)]

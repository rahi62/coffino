import os

from django.core.management.base import BaseCommand, CommandError

from apps.accounts.bootstrap import BootstrapError, bootstrap_business_owner


class Command(BaseCommand):
    help = "Create or safely reuse the first Cafino business, branch, and OWNER account without demo data."

    def add_arguments(self, parser):
        parser.add_argument("--business-name", required=True)
        parser.add_argument("--username", required=True)
        parser.add_argument("--email", default="")
        parser.add_argument("--branch-name", default="Main")
        parser.add_argument("--business-type", default="CAFE")
        parser.add_argument("--deployment-type", default="SAAS", choices=["LOCAL", "SAAS", "DEDICATED"])
        parser.add_argument("--password", default="", help="Prefer CAF_INO_BOOTSTRAP_OWNER_PASSWORD to avoid shell history.")
        parser.add_argument("--reset-password", action="store_true", help="Explicitly reset an existing matching OWNER password.")

    def handle(self, *args, **options):
        password = options["password"] or os.getenv("CAF_INO_BOOTSTRAP_OWNER_PASSWORD", "")
        try:
            result = bootstrap_business_owner(
                business_name=options["business_name"],
                username=options["username"],
                email=options["email"],
                branch_name=options["branch_name"],
                business_type=options["business_type"],
                deployment_type=options["deployment_type"],
                password=password,
                reset_password=options["reset_password"],
            )
        except BootstrapError as exc:
            message = str(exc)
            if not password and "password" in message.lower():
                message += " Set CAF_INO_BOOTSTRAP_OWNER_PASSWORD or pass --password."
            raise CommandError(message) from exc

        business=result["business"]
        branch=result["branch"]
        owner=result["owner"]
        if result["owner_created"]:
            self.stdout.write(
                self.style.SUCCESS(
                    "Bootstrap complete: "
                    f"business={business.id} ({'created' if result['business_created'] else 'reused'}), "
                    f"branch={branch.id} ({'created' if result['branch_created'] else 'reused'}), "
                    f"owner={owner.id}."
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"OWNER already exists; reused business={business.id}, branch={branch.id}, user={owner.id}."
                )
            )

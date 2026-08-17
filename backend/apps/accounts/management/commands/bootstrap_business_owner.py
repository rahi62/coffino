import os
import re

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.businesses.models import Branch, Business


def _validate_bootstrap_password(password, *, user, business_name):
    if len(password) < 12:
        raise CommandError("Owner password must be at least 12 characters.")
    if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        raise CommandError("Owner password must contain at least one Latin letter and one digit.")
    lowered = password.casefold()
    if user.username and user.username.casefold() in lowered:
        raise CommandError("Owner password must not contain the username.")
    normalized_business = "".join(str(business_name).casefold().split())
    if len(normalized_business) >= 4 and normalized_business in "".join(lowered.split()):
        raise CommandError("Owner password must not contain the business name.")
    try:
        validate_password(password, user=user)
    except ValidationError as exc:
        raise CommandError("Password validation failed: " + "; ".join(exc.messages)) from exc


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

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()
        business_name = options["business_name"].strip()
        username = options["username"].strip()
        email = options["email"].strip()
        branch_name = options["branch_name"].strip()
        business_type = options["business_type"].strip().upper()
        deployment_type = options["deployment_type"].strip().upper()
        password = options["password"] or os.getenv("CAF_INO_BOOTSTRAP_OWNER_PASSWORD", "")

        if not business_name or not username or not branch_name:
            raise CommandError("business-name, username, and branch-name must not be blank.")
        if len(business_name) > 160 or len(branch_name) > 160:
            raise CommandError("Business/branch name is too long.")
        if len(business_type) > 32:
            raise CommandError("business-type is too long.")

        businesses = list(Business.objects.filter(name=business_name).order_by("id")[:2])
        if len(businesses) > 1:
            raise CommandError("More than one business has this exact name; use a unique business name before bootstrapping.")
        if businesses:
            business = businesses[0]
            if business.deployment_type != deployment_type:
                raise CommandError(
                    f"Existing business deployment_type is {business.deployment_type}, not {deployment_type}."
                )
            if not business.is_active:
                business.is_active = True
                business.save(update_fields=["is_active", "updated_at"])
            business_created = False
        else:
            business = Business.objects.create(
                name=business_name,
                business_type=business_type,
                deployment_type=deployment_type,
                is_active=True,
            )
            business_created = True

        branches = list(Branch.objects.filter(business=business, name=branch_name).order_by("id")[:2])
        if len(branches) > 1:
            raise CommandError("More than one branch has this exact name in the business; resolve duplicates first.")
        if branches:
            branch = branches[0]
            branch_created = False
            if not branch.is_active:
                branch.is_active = True
                branch.save(update_fields=["is_active", "updated_at"])
        else:
            branch = Branch.objects.create(business=business, name=branch_name, is_active=True)
            branch_created = True

        existing = User.objects.filter(username=username).first()
        if existing:
            if existing.business_id != business.id or existing.role != User.Role.OWNER:
                raise CommandError("Username already belongs to another business or non-OWNER account.")
            changed = []
            if not existing.is_active:
                existing.is_active = True
                changed.append("is_active")
            if email and existing.email != email:
                existing.email = email
                changed.append("email")
            if options["reset_password"]:
                if not password:
                    raise CommandError("Password is required when --reset-password is used.")
                _validate_bootstrap_password(password, user=existing, business_name=business_name)
                existing.set_password(password)
                changed.append("password")
            if changed:
                existing.save(update_fields=changed)
            self.stdout.write(
                self.style.SUCCESS(
                    f"OWNER already exists; reused business={business.id}, branch={branch.id}, user={existing.id}."
                )
            )
            return

        if not password:
            raise CommandError(
                "Owner password is required. Set CAF_INO_BOOTSTRAP_OWNER_PASSWORD or pass --password."
            )
        candidate = User(
            username=username,
            email=email,
            business=business,
            branch=None,
            role=User.Role.OWNER,
            is_active=True,
        )
        _validate_bootstrap_password(password, user=candidate, business_name=business_name)
        candidate.set_password(password)
        candidate.save()

        self.stdout.write(
            self.style.SUCCESS(
                "Bootstrap complete: "
                f"business={business.id} ({'created' if business_created else 'reused'}), "
                f"branch={branch.id} ({'created' if branch_created else 'reused'}), "
                f"owner={candidate.id}."
            )
        )

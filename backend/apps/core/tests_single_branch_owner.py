from django.core.exceptions import PermissionDenied
from django.test import TestCase

from apps.accounts.models import User
from apps.businesses.models import Branch, Business, BusinessModule
from apps.core.tenancy import can_access_branch, resolve_branch_for_user


class SingleBranchOwnerTests(TestCase):
    def setUp(self):
        self.business = Business.objects.create(name="Single branch cafe")
        self.branch = Branch.objects.create(business=self.business, name="Main", is_active=True)
        BusinessModule.objects.create(business=self.business, key="MULTI_BRANCH", enabled=False)
        self.owner = User.objects.create_user(
            username="branchless-owner", password="test-password",
            business=self.business, role=User.Role.OWNER,
        )
        self.other = Business.objects.create(name="Other cafe")
        self.foreign_branch = Branch.objects.create(
            business=self.other, name="Foreign", is_active=True,
        )

    def test_owner_can_use_sole_active_branch_without_user_branch_assignment(self):
        self.assertTrue(can_access_branch(self.owner, self.branch))
        self.assertEqual(resolve_branch_for_user(self.owner), self.branch)
        self.assertEqual(resolve_branch_for_user(self.owner, self.branch.id), self.branch)

    def test_does_not_allow_other_business(self):
        self.assertFalse(can_access_branch(self.owner, self.foreign_branch))
        with self.assertRaises(PermissionDenied):
            resolve_branch_for_user(self.owner, self.foreign_branch.id)

    def test_two_active_branches_require_explicit_authorization(self):
        Branch.objects.create(business=self.business, name="Second", is_active=True)
        self.assertFalse(can_access_branch(self.owner, self.branch))
        with self.assertRaises(PermissionDenied):
            resolve_branch_for_user(self.owner)

    def test_inactive_branch_does_not_qualify_as_sole_active_branch(self):
        self.branch.is_active = False
        self.branch.save(update_fields=["is_active"])
        self.assertFalse(can_access_branch(self.owner, self.branch))
        with self.assertRaises(PermissionDenied):
            resolve_branch_for_user(self.owner)

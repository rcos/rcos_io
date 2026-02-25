from django.core.management.base import BaseCommand, CommandError

from portal.models import User


class Command(BaseCommand):
    help = "Delete all non-verified (unapproved) users that have never logged in. Staff and superusers are never deleted."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show how many users would be deleted without actually deleting them.",
        )
        parser.add_argument(
            "--no-input",
            action="store_true",
            help="Skip the confirmation prompt.",
        )

    def handle(self, *args, **options):
        unverified_users = User.objects.filter(
            is_approved=False,
            is_staff=False,
            is_superuser=False,
            last_login__isnull=True,
        )
        count = unverified_users.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS("No unverified users found. Nothing to do."))
            return

        if options["dry_run"]:
            self.stdout.write(self.style.WARNING(f"[DRY RUN] Would delete {count} unverified user(s)."))
            return

        if not options["no_input"]:
            confirm = input(
                f"This will permanently delete {count} unverified user(s). "
                "Are you sure? [y/N] "
            )
            if confirm.lower() != "y":
                self.stdout.write(self.style.NOTICE("Aborted."))
                return

        deleted_count, _ = unverified_users.delete()
        self.stdout.write(self.style.SUCCESS(f"Successfully deleted {deleted_count} unverified user(s)."))

"""Audit R2 storage: list real object keys and compare with the URLs Django
generates for stored media files. Helps spot prefix mismatches (404s).

    python manage.py r2_audit

Requires USE_R2=True and valid R2_* credentials.
"""

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "List R2 bucket keys and the URLs Django generates for media files."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=50,
                            help="Max object keys to list (default 50).")

    def handle(self, *args, **options):
        if not getattr(settings, "USE_R2", False):
            raise CommandError("USE_R2 is not True — nothing on R2 to audit.")

        import boto3

        client = boto3.client(
            "s3",
            endpoint_url=settings.AWS_S3_ENDPOINT_URL,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name="auto",
        )
        bucket = settings.AWS_STORAGE_BUCKET_NAME

        self.stdout.write(self.style.MIGRATE_HEADING(
            f"\n== Config ==\n"
            f"  bucket           : {bucket}\n"
            f"  endpoint         : {settings.AWS_S3_ENDPOINT_URL}\n"
            f"  public domain    : {settings.AWS_S3_CUSTOM_DOMAIN}\n"
            f"  media location   : {settings.STORAGES['default'].get('OPTIONS', {}).get('location', '')!r}\n"
            f"  static location  : {settings.STORAGES['staticfiles'].get('OPTIONS', {}).get('location', '')!r}\n"
            f"  STATIC_URL       : {settings.STATIC_URL}"
        ))

        # -- real keys in the bucket --
        limit = options["limit"]
        self.stdout.write(self.style.MIGRATE_HEADING(
            f"\n== Real object keys in bucket (first {limit}) =="))
        resp = client.list_objects_v2(Bucket=bucket, MaxKeys=limit)
        keys = [o["Key"] for o in resp.get("Contents", [])]
        if not keys:
            self.stdout.write("  (bucket is empty)")
        for k in keys:
            self.stdout.write(f"  {k}")
        key_set = set(keys)

        # -- URLs Django generates for stored media, and whether the key exists --
        self.stdout.write(self.style.MIGRATE_HEADING(
            "\n== Generated media URLs vs. real keys =="))
        from catalog.models import Category, Product
        from projects.models import Project
        from core.models import Certificate

        checked = 0
        for model, field in [
            (Category, "image"), (Product, "main_image"),
            (Project, "cover"), (Certificate, "image"),
        ]:
            for obj in model.objects.exclude(**{field: ""})[:10]:
                f = getattr(obj, field)
                if not f:
                    continue
                # The key Django expects = location + stored name.
                loc = settings.STORAGES["default"].get("OPTIONS", {}).get("location", "")
                expected_key = f"{loc}/{f.name}".lstrip("/") if loc else f.name
                exists = "OK " if expected_key in key_set else "404"
                if exists == "404":
                    # confirm against R2 directly (listing is capped at --limit)
                    try:
                        client.head_object(Bucket=bucket, Key=expected_key)
                        exists = "OK "
                    except Exception:
                        pass
                style = self.style.SUCCESS if exists == "OK " else self.style.ERROR
                self.stdout.write(style(
                    f"  [{exists}] {f.url}\n         key={expected_key}"))
                checked += 1

        if not checked:
            self.stdout.write("  (no media records with images found)")
        self.stdout.write("")

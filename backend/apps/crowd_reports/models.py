import uuid
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

# Deliverable 2 business rule: Current Time - Report Time <= 45 minutes.
CROWD_REPORT_TTL = timedelta(minutes=45)


class CrowdLevel(models.TextChoices):
    EMPTY = "empty", "Empty"
    MODERATE = "moderate", "Moderate"
    PACKED = "packed", "Packed"


class CrowdReportQuerySet(models.QuerySet):
    def current(self, now=None):
        now = now or timezone.now()
        return self.filter(reported_at__gte=now - CROWD_REPORT_TTL)


class CrowdReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    location = models.ForeignKey(
        "locations.Location", on_delete=models.CASCADE, related_name="crowd_reports",
        db_index=False,  # covered by the (location, -reported_at) composite index
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="crowd_reports",
        db_index=False,  # covered by the (user, -reported_at) composite index
    )
    level = models.CharField(max_length=10, choices=CrowdLevel.choices)
    reported_at = models.DateTimeField(default=timezone.now)

    objects = CrowdReportQuerySet.as_manager()

    class Meta:
        db_table = "crowd_reports_crowd_report"
        ordering = ["-reported_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(level__in=[c.value for c in CrowdLevel]),
                name="crowd_report_level_valid",
            ),
        ]
        indexes = [
            # Latest valid report per location (Location Details / Redis cache refill).
            models.Index(fields=["location", "-reported_at"], name="crowd_loc_reported_idx"),
            # Per-user history and rate limiting (e.g. one report per location per N minutes).
            models.Index(fields=["user", "-reported_at"], name="crowd_user_reported_idx"),
            # Global time scans: cleanup/archival of expired reports.
            models.Index(fields=["reported_at"], name="crowd_reported_at_idx"),
        ]

    def __str__(self):
        return f"{self.location_id} {self.level} @ {self.reported_at:%Y-%m-%d %H:%M}"

    def is_current(self, now=None):
        now = now or timezone.now()
        return now - self.reported_at <= CROWD_REPORT_TTL
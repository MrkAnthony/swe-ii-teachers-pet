from datetime import timedelta

from django.core.cache import cache
from django.utils import timezone

from .models import CrowdLevel, CrowdReport

# one report per student per location every 10 min
REPORT_COOLDOWN = timedelta(minutes=10)
STATUS_CACHE_SECONDS = 60


class LocationNotActive(Exception):
    pass


class ReportTooSoon(Exception):
    def __init__(self, retry_after):
        self.retry_after = int(retry_after)


def status_cache_key(location_id):
    return f"crowd_status:{location_id}"


def submit_report(user, location, level):
    if not location.is_active:
        raise LocationNotActive()

    now = timezone.now()
    last = (
        CrowdReport.objects.filter(user=user, location=location, reported_at__gt=now - REPORT_COOLDOWN)
        .order_by("-reported_at")
        .first()
    )
    if last:
        wait = (last.reported_at + REPORT_COOLDOWN - now).total_seconds()
        raise ReportTooSoon(max(wait, 1))

    report = CrowdReport.objects.create(user=user, location=location, level=level)
    cache.delete(status_cache_key(location.pk))
    return report


def get_location_status(location_id):
    key = status_cache_key(location_id)
    status = cache.get(key)
    if status is not None:
        return status

    reports = CrowdReport.objects.current().filter(location_id=location_id).order_by("-reported_at")
    newest = reports.first()

    status = {
        "level": newest.level if newest else None,
        "level_label": CrowdLevel(newest.level).label if newest else "No recent reports",
        "last_reported_at": newest.reported_at.isoformat() if newest else None,
        "report_count": reports.count(),
    }
    cache.set(key, status, STATUS_CACHE_SECONDS)
    return status

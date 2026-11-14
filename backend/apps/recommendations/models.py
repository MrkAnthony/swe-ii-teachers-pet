import uuid

from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.db import models


class RecommendationRequest(models.Model):
    """
    One "recommend me a spot" request: the preferences a student picked (S7.1)
    and when. RecommendationService fills RecommendedLocation rows for it.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="recommendation_requests",
        db_index=False,  # covered by the (user, -created_at) composite index
    )
    # e.g. {"noise_level": "quiet", "amenities": ["outlets", "whiteboard"],
    #       "max_crowd": "moderate", "study_type": "group", "open_now": true}
    preferences = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    locations = models.ManyToManyField(
        "locations.Location", through="RecommendedLocation", related_name="+", blank=True
    )

    class Meta:
        db_table = "recommendations_request"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"], name="rec_req_user_created_idx"),
            # Analytics: "how many students asked for quiet + outlets?"
            GinIndex(fields=["preferences"], name="rec_req_prefs_gin_idx"),
        ]


class RecommendedLocation(models.Model):
    """A ranked location returned for a RecommendationRequest."""

    request = models.ForeignKey(
        RecommendationRequest, on_delete=models.CASCADE, related_name="results",
        db_index=False,  # covered by the (request, rank) unique constraint
    )
    location = models.ForeignKey(
        "locations.Location", on_delete=models.CASCADE, related_name="recommended_in"
    )
    rank = models.PositiveSmallIntegerField()
    score = models.DecimalField(max_digits=6, decimal_places=3)

    class Meta:
        db_table = "recommendations_recommended_location"
        ordering = ["request", "rank"]
        constraints = [
            models.UniqueConstraint(fields=["request", "rank"], name="rec_result_rank_uniq"),
            models.UniqueConstraint(fields=["request", "location"], name="rec_result_location_uniq"),
            models.CheckConstraint(condition=models.Q(rank__gte=1), name="rec_result_rank_positive"),
        ]
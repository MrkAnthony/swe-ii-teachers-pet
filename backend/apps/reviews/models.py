import uuid

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Review(models.Model):
    """Student feedback for a location (Deliverable 2 class model; S8.1, S8.2)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    location = models.ForeignKey(
        "locations.Location", on_delete=models.CASCADE, related_name="reviews",
        db_index=False,  # covered by the (location, -created_at) composite index
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews",
        db_index=False,  # covered by the (user, location) unique constraint
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True)
    # Moderation: admins can hide abusive reviews without deleting them.
    is_visible = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "reviews_review"
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(rating__gte=1, rating__lte=5), name="review_rating_1_to_5"
            ),
            # One review per student per location; they edit it instead of posting again.
            models.UniqueConstraint(fields=["user", "location"], name="review_one_per_user_location"),
        ]
        indexes = [
            # Location Details page: newest visible reviews for a location.
            models.Index(
                fields=["location", "-created_at"], name="review_loc_created_idx",
                condition=models.Q(is_visible=True),
            ),
        ]

    def __str__(self):
        return f"{self.rating}/5 for {self.location_id} by {self.user_id}"
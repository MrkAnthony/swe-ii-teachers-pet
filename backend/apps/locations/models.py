import uuid

from django.contrib.postgres.indexes import GinIndex, OpClass
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models.functions import Lower


class NoiseLevel(models.TextChoices):
    SILENT = "silent", "Silent"
    QUIET = "quiet", "Quiet"
    MODERATE = "moderate", "Moderate"
    LOUD = "loud", "Loud"


class Location(models.Model):
    """An official FIU study location (Deliverable 2 class model + S2.x requirements)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150)
    building = models.CharField(max_length=150)
    floor = models.CharField(max_length=20, blank=True)
    room = models.CharField(max_length=50, blank=True)
    campus = models.CharField(max_length=50, default="MMC")
    description = models.TextField(blank=True)
    noise_level = models.CharField(max_length=10, choices=NoiseLevel.choices, default=NoiseLevel.QUIET)
    capacity = models.PositiveIntegerField(null=True, blank=True)
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
    )
    # Admins deactivate rather than delete so reviews / crowd history survive.
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    amenities = models.ManyToManyField(
        "Amenity", through="LocationAmenity", related_name="locations", blank=True
    )

    class Meta:
        db_table = "locations_location"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                Lower("name"), Lower("building"), name="locations_location_name_building_uniq"
            ),
            models.CheckConstraint(
                condition=models.Q(latitude__gte=-90, latitude__lte=90)
                          & models.Q(longitude__gte=-180, longitude__lte=180),
                name="locations_location_coords_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(noise_level__in=[n.value for n in NoiseLevel]),
                name="locations_location_noise_valid",
            ),
        ]
        indexes = [
            # Keyword search (S3.1): fast ILIKE '%term%' on name and building via pg_trgm.
            GinIndex(OpClass(Lower("name"), name="gin_trgm_ops"), name="loc_name_trgm_idx"),
            GinIndex(OpClass(Lower("building"), name="gin_trgm_ops"), name="loc_building_trgm_idx"),
            # Filtering (S3.2): active locations by noise level / campus.
            models.Index(
                fields=["noise_level"], name="loc_active_noise_idx",
                condition=models.Q(is_active=True),
            ),
            models.Index(fields=["campus", "is_active"], name="loc_campus_active_idx"),
        ]

    def __str__(self):
        return f"{self.name} ({self.building})"


class Amenity(models.Model):
    """A feature such as outlets, whiteboards, group tables."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=80)
    slug = models.SlugField(max_length=80, unique=True)

    class Meta:
        db_table = "locations_amenity"
        ordering = ["name"]
        verbose_name_plural = "amenities"
        constraints = [
            models.UniqueConstraint(Lower("name"), name="locations_amenity_name_ci_uniq"),
        ]

    def __str__(self):
        return self.name


class LocationAmenity(models.Model):
    """LOCATION_AMENITY join table (Deliverable 4, Data Access Layer)."""

    # db_index=False: the (location, amenity) unique constraint already indexes location first.
    location = models.ForeignKey(Location, on_delete=models.CASCADE, db_index=False)
    amenity = models.ForeignKey(Amenity, on_delete=models.CASCADE, related_name="location_links")

    class Meta:
        db_table = "locations_location_amenity"
        constraints = [
            models.UniqueConstraint(fields=["location", "amenity"], name="location_amenity_uniq"),
        ]


class DayOfWeek(models.IntegerChoices):
    MONDAY = 0, "Monday"
    TUESDAY = 1, "Tuesday"
    WEDNESDAY = 2, "Wednesday"
    THURSDAY = 3, "Thursday"
    FRIDAY = 4, "Friday"
    SATURDAY = 5, "Saturday"
    SUNDAY = 6, "Sunday"


class LocationHours(models.Model):
    """Operating hours per weekday (S2.1, filter by hours in S3.2). No row for a day = closed."""

    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name="hours", db_index=False)
    day_of_week = models.PositiveSmallIntegerField(choices=DayOfWeek.choices)
    opens_at = models.TimeField()
    closes_at = models.TimeField()  # may be <= opens_at for past-midnight closing

    class Meta:
        db_table = "locations_location_hours"
        ordering = ["location", "day_of_week"]
        constraints = [
            models.UniqueConstraint(fields=["location", "day_of_week"], name="location_hours_day_uniq"),
            models.CheckConstraint(
                condition=models.Q(day_of_week__gte=0, day_of_week__lte=6),
                name="location_hours_day_valid",
            ),
        ]
        indexes = [
            # "Open now" filter: find locations open on a given weekday at a given time.
            models.Index(fields=["day_of_week", "opens_at", "closes_at"], name="loc_hours_open_now_idx"),
        ]
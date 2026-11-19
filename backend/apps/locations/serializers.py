from django.utils import timezone
from rest_framework import serializers

from .models import Amenity, Location, LocationHours, NoiseLevel
from .services import LocationFilters, LocationService, campus_tz


class _CSVListField(serializers.ListField):
    """Accepts ?amenities=wifi,outlets as well as ?amenities=wifi&amenities=outlets."""

    def get_value(self, dictionary):
        raw = dictionary.getlist(self.field_name) if hasattr(dictionary, "getlist") else []
        values = [v.strip() for item in raw for v in item.split(",") if v.strip()]
        return values or serializers.empty


class LocationSearchParamsSerializer(serializers.Serializer):
    """Validates query params for GET /locations/ and turns them into LocationFilters."""

    q = serializers.CharField(required=False, allow_blank=True, max_length=150, trim_whitespace=True)
    noise_level = _CSVListField(
        child=serializers.ChoiceField(choices=NoiseLevel.choices), required=False
    )
    campus = serializers.CharField(required=False, allow_blank=True, max_length=50)
    amenities = _CSVListField(child=serializers.SlugField(max_length=80), required=False)
    min_capacity = serializers.IntegerField(required=False, min_value=1)
    open_now = serializers.BooleanField(required=False, default=False)
    # A naive ?open_at=2026-11-16T10:00 means 10 AM on campus, not 10 AM UTC.
    open_at = serializers.DateTimeField(required=False, default_timezone=campus_tz())

    def to_filters(self) -> LocationFilters:
        d = self.validated_data
        open_at = d.get("open_at") or (timezone.now() if d.get("open_now") else None)
        return LocationFilters(
            q=d.get("q", ""),
            noise_levels=tuple(dict.fromkeys(d.get("noise_level", []))),
            campus=d.get("campus", ""),
            amenities=tuple(dict.fromkeys(d.get("amenities", []))),
            min_capacity=d.get("min_capacity"),
            open_at=open_at,
        )


class AmenitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Amenity
        fields = ["slug", "name"]


class LocationHoursSerializer(serializers.ModelSerializer):
    day = serializers.CharField(source="get_day_of_week_display")

    class Meta:
        model = LocationHours
        fields = ["day_of_week", "day", "opens_at", "closes_at"]


class _OpenStatusMixin(serializers.Serializer):
    is_open_now = serializers.SerializerMethodField()

    def get_is_open_now(self, obj) -> bool:
        return LocationService.open_status(obj, self.context.get("now")).is_open


class LocationCardSerializer(_OpenStatusMixin, serializers.ModelSerializer):
    """Compact shape for LocationCard on the results screen."""

    amenities = AmenitySerializer(many=True, read_only=True)

    class Meta:
        model = Location
        fields = [
            "id", "name", "building", "floor", "room", "campus",
            "noise_level", "capacity", "amenities", "is_open_now",
        ]


class LocationDetailSerializer(_OpenStatusMixin, serializers.ModelSerializer):
    """RPT-01 fields 1–3 (name, information, amenities) plus hours and coordinates."""

    amenities = AmenitySerializer(many=True, read_only=True)
    hours = LocationHoursSerializer(many=True, read_only=True)
    closes_at = serializers.SerializerMethodField()

    class Meta:
        model = Location
        fields = [
            "id", "name", "building", "floor", "room", "campus", "description",
            "noise_level", "capacity", "latitude", "longitude",
            "amenities", "hours", "is_open_now", "closes_at", "updated_at",
        ]

    def get_closes_at(self, obj):
        return LocationService.open_status(obj, self.context.get("now")).closes_at
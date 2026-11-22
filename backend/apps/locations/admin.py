from django.contrib import admin

from .models import (
    Location,
    Amenity,
    LocationAmenity,
    LocationHours,
)


class LocationHoursInline(admin.TabularInline):
    model = LocationHours
    extra = 0


class LocationAmenityInline(admin.TabularInline):
    model = LocationAmenity
    extra = 0


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "building",
        "campus",
        "floor",
        "noise_level",
        "capacity",
        "is_active",
        "updated_at",
    )

    list_filter = (
        "campus",
        "noise_level",
        "is_active",
    )

    search_fields = (
        "name",
        "building",
        "description",
    )

    list_editable = ("is_active",)

    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
    )

    inlines = [
        LocationHoursInline,
        LocationAmenityInline,
    ]

    fieldsets = (
        ("Basic Information", {
            "fields": (
                "name",
                "building",
                "campus",
                "floor",
                "room",
                "description",
            )
        }),
        ("Study Environment", {
            "fields": (
                "noise_level",
                "capacity",
            )
        }),
        ("Map & Navigation", {
            "fields": (
                "latitude",
                "longitude",
            )
        }),
        ("Status", {
            "fields": (
                "is_active",
            )
        }),
        ("System Information", {
            "fields": (
                "id",
                "created_at",
                "updated_at",
            )
        }),
    )


@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}

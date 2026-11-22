from django.shortcuts import render


from decimal import Decimal

from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.locations.models import NoiseLevel
from apps.locations.services import LocationService
from apps.crowd_reports.models import CrowdReport
from .models import RecommendationRequest, RecommendedLocation


class RecommendationView(APIView):
    """
    FR-05: Recommend study locations based on student preferences.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        preferences = request.data

        if not isinstance(preferences, dict):
            return Response(
                {"detail": "Preferences must be a JSON object."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        campus = preferences.get("campus", "")
        noise_level = preferences.get("noise_level", "")
        amenities = preferences.get("amenities", [])
        max_crowd = preferences.get("max_crowd", "")
        open_now = preferences.get("open_now", False)

        if not isinstance(amenities, list) or not all(
            isinstance(item, str) for item in amenities
        ):
            return Response(
                {"detail": "Amenities must be a list of strings."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        valid_noise = [choice[0] for choice in NoiseLevel.choices]

        if noise_level and noise_level not in valid_noise:
            return Response(
                {"detail": "Invalid noise level."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if max_crowd and max_crowd not in [
            "empty", "moderate", "packed"
        ]:
            return Response(
                {"detail": "Invalid maximum crowd level."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not isinstance(open_now, bool):
            return Response(
                {"detail": "open_now must be true or false."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        now = timezone.now()

        # Get active locations and their related information.
        locations = LocationService.public_queryset().prefetch_related(
            "amenities",
            "hours",
        )

        # Get the latest recent crowd report for each location.
        recent_reports = (
            CrowdReport.objects.current(now)
            .order_by("location_id", "-reported_at")
        )

        crowd_by_location = {}

        for report in recent_reports:
            crowd_by_location.setdefault(
                report.location_id, report.level
            )

        # Save the student's recommendation request.
        recommendation_request = RecommendationRequest.objects.create(
            user=request.user if request.user.is_authenticated else None,
            preferences=preferences,
        )

        crowd_order = {
            "empty": 1,
            "moderate": 2,
            "packed": 3,
        }

        ranked_locations = []

        for location in locations:
            score = 0.0

            # Campus preference.
            if campus:
                if location.campus.lower() == campus.lower():
                    score += 20
                else:
                    score -= 10

            # Noise preference.
            if noise_level:
                if location.noise_level == noise_level:
                    score += 25
                else:
                    score -= 5

            # Amenity preferences.
            available_amenities = {
                amenity.slug for amenity in location.amenities.all()
            }

            for amenity in amenities:
                if amenity in available_amenities:
                    score += 8
                else:
                    score -= 3

            # Current crowd level.
            crowd = crowd_by_location.get(location.id)

            if crowd == "empty":
                score += 20
            elif crowd == "moderate":
                score += 10
            elif crowd == "packed":
                score -= 15

            # Maximum acceptable crowd level.
            if max_crowd and crowd:
                if crowd_order[crowd] > crowd_order[max_crowd]:
                    continue

            # Opening status.
            opening_status = LocationService.open_status(
                location, now
            )

            if open_now and not opening_status.is_open:
                continue

            if opening_status.is_open:
                score += 10

            ranked_locations.append({
                "location": location,
                "score": round(score, 3),
                "crowd": crowd,
                "is_open_now": opening_status.is_open,
            })

        # Highest score first.
        ranked_locations.sort(
            key=lambda item: (
                -item["score"],
                item["location"].name.lower(),
            )
        )

        # Save the top 10 recommendations.
        top_locations = ranked_locations[:10]

        RecommendedLocation.objects.bulk_create([
            RecommendedLocation(
                request=recommendation_request,
                location=item["location"],
                rank=index,
                score=Decimal(f'{item["score"]:.3f}'),
            )
            for index, item in enumerate(top_locations, start=1)
        ])

        results = []

        for index, item in enumerate(top_locations, start=1):
            location = item["location"]

            results.append({
                "id": str(location.id),
                "name": location.name,
                "building": location.building,
                "campus": location.campus,
                "floor": location.floor,
                "noise_level": location.noise_level,
                "amenities": [
                    amenity.slug
                    for amenity in location.amenities.all()
                ],
                "crowd_level": item["crowd"],
                "is_open_now": item["is_open_now"],
                "rank": index,
                "score": item["score"],
            })

        return Response({
            "request_id": str(recommendation_request.id),
            "preferences": preferences,
            "count": len(results),
            "results": results,
        }, status=status.HTTP_200_OK)


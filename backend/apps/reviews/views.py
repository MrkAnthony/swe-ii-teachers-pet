import uuid

from django.db.models import Avg
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Review
from .serializers import ReviewSerializer


class ReviewView(APIView):
    """
    GET  /api/reviews/?location=<id>   reviews for one location (anyone)
    POST /api/reviews/                 {"location", "rating", "comment"} (logged in)
    """

    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        location_id = request.query_params.get("location")
        try:
            uuid.UUID(str(location_id))
        except ValueError:
            raise ValidationError({"location": "Send a valid location id, e.g. ?location=<id>"})

        reviews = Review.objects.filter(location_id=location_id, is_visible=True).order_by("-created_at")
        average = reviews.aggregate(avg=Avg("rating"))["avg"]

        return Response({
            "count": reviews.count(),
            "average_rating": round(average, 1) if average else None,
            "results": ReviewSerializer(reviews, many=True).data,
        })

    def post(self, request):
        serializer = ReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        location = serializer.validated_data["location"]

        if not location.is_active:
            raise ValidationError({"location": "This study location is not available right now."})
        if Review.objects.filter(user=request.user, location=location).exists():
            raise ValidationError({"detail": "You already reviewed this location."})

        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

from django.http import Http404
from django.utils import timezone
from rest_framework import generics
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    LocationCardSerializer,
    LocationDetailSerializer,
    LocationSearchParamsSerializer,
)
from .services import LocationNotFound, LocationService


class LocationPagination(PageNumberPagination):
    """
    Set on the view so the response is always {"count", "next", "previous", "results"},
    whatever REST_FRAMEWORK settings say. The frontend can rely on that shape.
    """

    page_size = 20
    page_size_query_param = "page_size"  # e.g. ?page_size=50
    max_page_size = 100


class LocationListView(generics.ListAPIView):
    """GET /locations/?q=&noise_level=&campus=&amenities=&min_capacity=&open_now= (FR-01)."""

    serializer_class = LocationCardSerializer
    pagination_class = LocationPagination
    permission_classes = [AllowAny]  # guests may search (D2 actor table)

    def get_queryset(self):
        params = LocationSearchParamsSerializer(data=self.request.query_params)
        params.is_valid(raise_exception=True)  # -> 400 with field errors
        return LocationService.search(params.to_filters())

    def get_serializer_context(self):
        return {**super().get_serializer_context(), "now": timezone.now()}


class LocationDetailView(APIView):
    """GET /locations/<uuid>/ (FR-02, RPT-01)."""

    permission_classes = [AllowAny]

    def get(self, request, pk):
        try:
            location = LocationService.get_location(pk)
        except LocationNotFound:
            raise Http404("Location not found.")
        ser = LocationDetailSerializer(location, context={"request": request, "now": timezone.now()})
        return Response(ser.data)


class LocationFilterOptionsView(APIView):
    """GET /locations/filters/ — options for the SearchFilters component."""

    permission_classes = [AllowAny]

    def get(self, request):
        return Response(LocationService.filter_options())
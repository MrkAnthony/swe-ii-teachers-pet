from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import Throttled, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.locations.models import Location

from . import services
from .serializers import CrowdReportSerializer


class CrowdReportCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CrowdReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            report = services.submit_report(
                request.user,
                serializer.validated_data["location"],
                serializer.validated_data["level"],
            )
        except services.LocationNotActive:
            raise ValidationError({"location": "This study location is not available right now."})
        except services.ReportTooSoon as e:
            raise Throttled(wait=e.retry_after, detail="You already reported this spot a few minutes ago.")

        return Response(CrowdReportSerializer(report).data, status=status.HTTP_201_CREATED)


class LocationCrowdStatusView(APIView):
    def get(self, request, location_id):
        get_object_or_404(Location, pk=location_id)
        return Response(services.get_location_status(location_id))

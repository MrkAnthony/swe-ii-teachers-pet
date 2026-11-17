from rest_framework import serializers

from .models import CrowdReport


class CrowdReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = CrowdReport
        fields = ["id", "location", "level", "reported_at"]
        read_only_fields = ["id", "reported_at"]

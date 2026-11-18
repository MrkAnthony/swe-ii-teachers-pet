from rest_framework import serializers

from .models import Review


class ReviewSerializer(serializers.ModelSerializer):
    comment = serializers.CharField(max_length=1000, required=False, allow_blank=True)

    class Meta:
        model = Review
        # no user field, other students don't need to see who wrote it
        fields = ["id", "location", "rating", "comment", "created_at"]
        read_only_fields = ["id", "created_at"]

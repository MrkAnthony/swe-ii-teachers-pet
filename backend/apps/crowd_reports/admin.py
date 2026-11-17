from django.contrib import admin

from .models import CrowdReport


@admin.register(CrowdReport)
class CrowdReportAdmin(admin.ModelAdmin):
    list_display = ["location", "level", "reported_at", "user"]
    list_filter = ["level"]


from django.contrib import admin
from django.urls import include, path
from django.http import JsonResponse


def health(request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health, name="health"),
    path("api/accounts/", include("apps.accounts.urls")),
    path("api/crowd-reports/", include("apps.crowd_reports.urls")),
    path("api/", include("apps.locations.urls")),
    path("api/reviews/", include("apps.reviews.urls")),
    path(
        "api/recommendations/",
        include("apps.recommendations.urls"),
    ),
]

from django.db import connection
from django.http import JsonResponse
from django_redis import get_redis_connection


def health(request):
    result = {"database": "ok", "cache": "ok"}

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception:
        result["database"] = "down"

    try:
        get_redis_connection("default").ping()
    except Exception:
        result["cache"] = "down"

    # app can still run without redis, but not without postgres
    code = 200 if result["database"] == "ok" else 503
    return JsonResponse(result, status=code)

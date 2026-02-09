from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse

from django.conf import settings
from django.conf.urls.static import static

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

# --------------------------------------------------
# HEALTH CHECK / HOME
# --------------------------------------------------
def home(request):
    return HttpResponse("Backend Running ✅ SplitBills")


# --------------------------------------------------
# URL PATTERNS
# --------------------------------------------------
urlpatterns = [
    path("", home),

    path("admin/", admin.site.urls),

    # 🔐 JWT AUTH
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # 🚀 CORE APIS
    path("api/", include("core.urls")),
]


# --------------------------------------------------
# MEDIA FILES (ONLY IN DEV)
# --------------------------------------------------
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )

from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    # Django administration panel
    path("admin/", admin.site.urls),

    # Audience Automation web application
    path("", include("web.urls")),
]

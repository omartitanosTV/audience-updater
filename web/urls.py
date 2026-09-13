from django.urls import path

from . import views


app_name = "web"

urlpatterns = [
    # Main dashboard
    path("", views.dashboard, name="dashboard"),

    # Audience configuration
    path("audiences/new/", views.audience_create, name="audience_create"),
    path(
        "audiences/<int:audience_id>/edit/",
        views.audience_edit,
        name="audience_edit",
    ),

    # Audience actions
    path(
        "audiences/<int:audience_id>/refresh/",
        views.refresh_audience,
        name="refresh_audience",
    ),
    path(
        "audiences/<int:audience_id>/toggle/",
        views.toggle_audience,
        name="toggle_audience",
    ),
    path(
        "audiences/<int:audience_id>/delete/",
        views.audience_delete,
        name="audience_delete",
    ),

    # Execution history
    path("history/", views.history, name="history"),
]

from django.urls import path
from .views import create_plot, plot_detail, delete_marker, create_plot_by_polygon, create_plot_by_map

app_name = "plots"

urlpatterns = [
    path("create/", create_plot, name="create_plot"),
    path("create/by-polygon/", create_plot_by_polygon, name="create_plot_by_polygon"),
    path("create/by-map/", create_plot_by_map, name="create_plot_by_map"),
    path("<int:plot_id>/", plot_detail, name="plot_detail"),
    path("<int:plot_id>/delete-marker/<int:marker_id>/", delete_marker, name="delete_marker"),
]
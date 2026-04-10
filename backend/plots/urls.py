from django.urls import path
from .views import (
    plot_list,
    plot_detail,
    delete_marker,
    create_plot_by_marker_coordinates,
    create_plot_by_map,
    owner_list,
    owner_create,
    plot_gallery,
)

app_name = "plots"

urlpatterns = [
    path("", plot_list, name="plot_list"),
    path("owners/", owner_list, name="owner_list"),
    path("owners/create/", owner_create, name="owner_create"),
    path(
        "create/by-marker-coordinates/",
        create_plot_by_marker_coordinates,
        name="create_plot_by_marker_coordinates",
    ),
    path("create/by-map/", create_plot_by_map, name="create_plot_by_map"),
    path("<int:plot_id>/gallery/", plot_gallery, name="plot_gallery"),
    path("<int:plot_id>/", plot_detail, name="plot_detail"),
    path("<int:plot_id>/delete-marker/<int:marker_id>/", delete_marker, name="delete_marker"),
]
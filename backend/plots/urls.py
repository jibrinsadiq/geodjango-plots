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
    delete_plot_media,
    buyer_register,
    buyer_create,
    buyer_login,
    buyer_logout,
    delete_plot_document,
    town_boundaries_geojson,

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
    path("<int:plot_id>/delete-media/<int:media_id>/", delete_plot_media, name="delete_plot_media"),

    path("buyers/register/", buyer_register, name="buyer_register"),
    path("buyers/create/", buyer_create, name="buyer_create"),
    path("buyers/login/", buyer_login, name="buyer_login"),
    path("buyers/logout/", buyer_logout, name="buyer_logout"),
    path(
    "<int:plot_id>/delete-document/<int:document_id>/",
    delete_plot_document,
    name="delete_plot_document",
),
    path("town-boundaries.geojson", town_boundaries_geojson, name="town_boundaries_geojson"),
   




]
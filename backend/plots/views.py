import json

from django.contrib import messages
from django.contrib.gis.geos import Point, Polygon
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PlotForm, MarkerForm, PlotPolygonForm, PlotMapForm
from .models import Plot, Marker
from .services import (
    build_polygon_from_markers,
    extract_markers_from_polygon,
    compute_plot_area,
    validate_plot_overlap,
    validate_plot_within_parent,
)



def create_plot(request):
    if request.method == "POST":
        form = PlotForm(request.POST)
        if form.is_valid():
            plot = form.save()
            messages.success(request, "Plot created. You can now add markers.")
            return redirect("plots:plot_detail", plot_id=plot.id)
    else:
        form = PlotForm()

    return render(request, "plots/create_plot.html", {"form": form})


def plot_detail(request, plot_id):
    plot = get_object_or_404(Plot, id=plot_id)
    markers = plot.markers.order_by("marker_order")

    edit_marker_id = request.GET.get("edit")
    marker_instance = None

    if edit_marker_id:
        marker_instance = get_object_or_404(Marker, id=edit_marker_id, plot=plot)

    if request.method == "POST":
        if "save_marker" in request.POST:
            if request.POST.get("marker_id"):
                marker_instance = get_object_or_404(
                    Marker, id=request.POST.get("marker_id"), plot=plot
                )
                form = MarkerForm(request.POST, instance=marker_instance)
            else:
                form = MarkerForm(request.POST)

            if form.is_valid():
                marker = form.save(commit=False)
                marker.plot = plot
                marker.point = Point(marker.longitude, marker.latitude, srid=4326)

                try:
                    marker.save()
                    messages.success(request, "Marker saved successfully.")
                    return redirect("plots:plot_detail", plot_id=plot.id)
                except Exception as e:
                    messages.error(request, f"Could not save marker: {e}")

        elif "generate_polygon" in request.POST:
            try:
                with transaction.atomic():
                    polygon = build_polygon_from_markers(plot)
                    plot.polygon = polygon
                    plot.save(update_fields=["polygon", "updated_at"])

                    area_sqm, area_hectares = compute_plot_area(plot)
                    plot.area_sqm = area_sqm
                    plot.area_hectares = area_hectares
                    plot.save(update_fields=["area_sqm", "area_hectares", "updated_at"])

                messages.success(request, "Polygon generated successfully.")
                return redirect("plots:plot_detail", plot_id=plot.id)
            except ValidationError as e:
                messages.error(request, str(e))
    else:
        form = MarkerForm(instance=marker_instance)

    polygon_coords = []
    if plot.polygon:
        polygon_coords = list(plot.polygon.coords[0])

    marker_data = [
        {
            "id": marker.id,
            "name": marker.marker_name,
            "order": marker.marker_order,
            "longitude": marker.longitude,
            "latitude": marker.latitude,
        }
        for marker in markers
    ]

    return render(
        request,
        "plots/plot_detail.html",
        {
            "plot": plot,
            "markers": markers,
            "form": form,
            "editing_marker": marker_instance,
            "polygon_coords": polygon_coords,
            "marker_data": marker_data,
        },
    )


def delete_marker(request, plot_id, marker_id):
    plot = get_object_or_404(Plot, id=plot_id)
    marker = get_object_or_404(Marker, id=marker_id, plot=plot)

    if request.method == "POST":
        marker.delete()
        messages.success(request, "Marker deleted successfully.")
        return redirect("plots:plot_detail", plot_id=plot.id)

    return render(
        request,
        "plots/delete_marker.html",
        {
            "plot": plot,
            "marker": marker,
        },
    )


def create_plot_by_polygon(request):
    if request.method == "POST":
        form = PlotPolygonForm(request.POST)
        if form.is_valid():
            polygon_text = form.cleaned_data["polygon_text"]

            try:
                coords = []
                for line in polygon_text.strip().splitlines():
                    if not line.strip():
                        continue

                    longitude_str, latitude_str = line.split(",")
                    longitude = float(longitude_str.strip())
                    latitude = float(latitude_str.strip())
                    coords.append((longitude, latitude))

                if len(coords) < 3:
                    raise ValidationError("A polygon must have at least 3 points.")

                if coords[0] != coords[-1]:
                    coords.append(coords[0])

                polygon = Polygon(coords, srid=4326)

                if not polygon.valid:
                    raise ValidationError("The coordinates do not form a valid polygon.")

                with transaction.atomic():
                    plot = form.save(commit=False)
                    plot.polygon = polygon
                    plot.save()

                    area_sqm, area_hectares = compute_plot_area(plot)
                    plot.area_sqm = area_sqm
                    plot.area_hectares = area_hectares
                    plot.save(update_fields=["area_sqm", "area_hectares", "updated_at"])

                    extract_markers_from_polygon(plot)

                messages.success(request, "Plot created from polygon and markers extracted.")
                return redirect("plots:plot_detail", plot_id=plot.id)

            except Exception as e:
                messages.error(request, f"Could not create polygon: {e}")
    else:
        form = PlotPolygonForm()

    return render(request, "plots/create_plot_by_polygon.html", {"form": form})


def create_plot_by_map(request):
    if request.method == "POST":
        form = PlotMapForm(request.POST)
        if form.is_valid():
            polygon_json = request.POST.get("polygon_json")

            try:
                if not polygon_json:
                    raise ValidationError("No polygon was drawn.")

                coords = json.loads(polygon_json)

                if len(coords) < 3:
                    raise ValidationError("A polygon must have at least 3 points.")

                polygon_coords = []
                for point in coords:
                    longitude = float(point["lng"])
                    latitude = float(point["lat"])
                    polygon_coords.append((longitude, latitude))

                if polygon_coords[0] != polygon_coords[-1]:
                    polygon_coords.append(polygon_coords[0])

                polygon = Polygon(polygon_coords, srid=4326)

                if not polygon.valid:
                    raise ValidationError("The drawn polygon is not valid.")

                with transaction.atomic():
                    plot = form.save(commit=False)
                    plot.polygon = polygon
                    plot.save()

                    area_sqm, area_hectares = compute_plot_area(plot)
                    plot.area_sqm = area_sqm
                    plot.area_hectares = area_hectares
                    plot.save(update_fields=["area_sqm", "area_hectares", "updated_at"])

                    extract_markers_from_polygon(plot)

                messages.success(request, "Plot created from map drawing.")
                return redirect("plots:plot_detail", plot_id=plot.id)

            except Exception as e:
                messages.error(request, f"Could not save drawn polygon: {e}")
    else:
        form = PlotMapForm()

    return render(request, "plots/create_plot_by_map.html", {"form": form})



def subdivide_plot_by_map(request, parent_plot_id):
    parent_plot = get_object_or_404(Plot, id=parent_plot_id)

    if not parent_plot.polygon:
        messages.error(request, "Parent plot has no polygon to subdivide.")
        return redirect("plots:plot_detail", plot_id=parent_plot.id)

    if request.method == "POST":
        form = ChildPlotForm(request.POST)
        if form.is_valid():
            polygon_json = request.POST.get("polygon_json")

            try:
                if not polygon_json:
                    raise ValidationError("No child polygon was drawn.")

                coords = json.loads(polygon_json)

                if len(coords) < 3:
                    raise ValidationError("A child polygon must have at least 3 points.")

                polygon_coords = []
                for point in coords:
                    longitude = float(point["lng"])
                    latitude = float(point["lat"])
                    polygon_coords.append((longitude, latitude))

                if polygon_coords[0] != polygon_coords[-1]:
                    polygon_coords.append(polygon_coords[0])

                child_polygon = Polygon(polygon_coords, srid=4326)

                if not child_polygon.valid:
                    raise ValidationError("The child polygon is not valid.")

                validate_plot_within_parent(child_polygon, parent_plot)
                validate_plot_overlap(child_polygon)

                with transaction.atomic():
                    child_plot = form.save(commit=False)
                    child_plot.parent_plot = parent_plot
                    child_plot.polygon = child_polygon
                    child_plot.save()

                    area_sqm, area_hectares = compute_plot_area(child_plot)
                    child_plot.area_sqm = area_sqm
                    child_plot.area_hectares = area_hectares
                    child_plot.save(update_fields=["area_sqm", "area_hectares", "updated_at"])

                    extract_markers_from_polygon(child_plot)

                messages.success(request, "Child plot created successfully.")
                return redirect("plots:plot_detail", plot_id=child_plot.id)

            except Exception as e:
                messages.error(request, f"Could not subdivide plot: {e}")
    else:
        form = ChildPlotForm()

    parent_polygon_coords = list(parent_plot.polygon.coords[0]) if parent_plot.polygon else []

    other_plots = Plot.objects.filter(
        polygon__isnull=False
    ).exclude(id=parent_plot.id)

    other_plot_data = []
    for plot in other_plots:
        other_plot_data.append({
            "id": plot.id,
            "name": plot.plot_name,
            "coords": list(plot.polygon.coords[0]),
            "is_child_of_parent": plot.parent_plot_id == parent_plot.id,
        })

    return render(
        request,
        "plots/subdivide_plot_by_map.html",
        {
            "parent_plot": parent_plot,
            "parent_polygon_coords": parent_polygon_coords,
            "other_plot_data": other_plot_data,
            "form": form,
        },
    )





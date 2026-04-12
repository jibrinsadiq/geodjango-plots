import json

from django.contrib import messages
from django.contrib.gis.geos import Point, Polygon
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.contrib.auth.models import Group, User
from .forms import BuyerLoginForm, BuyerRegistrationForm
from django.contrib.auth import authenticate, login, logout








from .forms import (
    MarkerForm,
    PlotMarkerCoordinatesForm,
    PlotMapForm,
    SplitPlotForm,
    OwnerForm,
    PlotOwnerAssignForm,
    PlotMediaForm,
)
from .models import Plot, Marker, Owner, PlotMedia

from .services import (
    build_polygon_from_markers,
    extract_markers_from_polygon,
    compute_plot_area,
    validate_plot_overlap,
    validate_plot_within_parent,
    split_plot_geometry,
    snap_polygon_vertices_to_parent,
)








def plot_detail(request, plot_id):
    plot = get_object_or_404(Plot, id=plot_id)
    markers = plot.markers.order_by("marker_order")

    edit_marker_id = request.GET.get("edit")
    marker_instance = None

    if edit_marker_id:
        marker_instance = get_object_or_404(Marker, id=edit_marker_id, plot=plot)

    form = MarkerForm(instance=marker_instance)
    owner_form = PlotOwnerAssignForm(instance=plot)
    media_form = PlotMediaForm()

    if request.method == "POST":
        if "save_marker" in request.POST:
            if request.POST.get("marker_id"):
                marker_instance = get_object_or_404(
                    Marker,
                    id=request.POST.get("marker_id"),
                    plot=plot,
                )
                form = MarkerForm(request.POST, instance=marker_instance)
            else:
                form = MarkerForm(request.POST)

            owner_form = PlotOwnerAssignForm(instance=plot)
            media_form = PlotMediaForm()

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

        elif "assign_owner" in request.POST:
            form = MarkerForm(instance=marker_instance)
            owner_form = PlotOwnerAssignForm(request.POST, instance=plot)
            media_form = PlotMediaForm()

            if owner_form.is_valid():
                owner_form.save()
                messages.success(request, "Plot owner and sales details updated successfully.")
                return redirect("plots:plot_detail", plot_id=plot.id)

        elif "upload_media" in request.POST:
            form = MarkerForm(instance=marker_instance)
            owner_form = PlotOwnerAssignForm(instance=plot)
            media_form = PlotMediaForm(request.POST, request.FILES)

            if media_form.is_valid():
                media = media_form.save(commit=False)
                media.plot = plot
                media.save()
                messages.success(request, "Media uploaded successfully.")
                return redirect("plots:plot_detail", plot_id=plot.id)

        elif "generate_polygon" in request.POST:
            form = MarkerForm(instance=marker_instance)
            owner_form = PlotOwnerAssignForm(instance=plot)
            media_form = PlotMediaForm()

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

    child_plots = plot.sub_plots.order_by("plot_name")

    child_plot_data = []
    for child in child_plots:
        if child.polygon:
            child_plot_data.append(
                {
                    "id": child.id,
                    "name": child.plot_name,
                    "coords": list(child.polygon.coords[0]),
                    "area_sqm": child.area_sqm,
                    "area_hectares": child.area_hectares,
                    "is_active": child.is_active,
                }
            )

    media_items = plot.media_files.order_by("-uploaded_at")
    image_items = media_items.filter(media_type="image")
    video_items = media_items.filter(media_type="video")

    return render(
        request,
        "plots/plot_detail.html",
        {
            "plot": plot,
            "markers": markers,
            "form": form,
            "owner_form": owner_form,
            "media_form": media_form,
            "editing_marker": marker_instance,
            "polygon_coords": polygon_coords,
            "marker_data": marker_data,
            "child_plots": child_plots,
            "child_plot_data": child_plot_data,
            "media_items": media_items,
            "image_items": image_items,
            "video_items": video_items,
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


def create_plot_by_marker_coordinates(request):
    if request.method == "POST":
        form = PlotMarkerCoordinatesForm(request.POST)
        if form.is_valid():
            marker_rows = form.cleaned_data["marker_rows"]

            try:
                parsed_markers = []
                seen_orders = set()

                for line_number, line in enumerate(marker_rows.strip().splitlines(), start=1):
                    if not line.strip():
                        continue

                    parts = [part.strip() for part in line.split(",")]

                    if len(parts) != 4:
                        raise ValidationError(
                            f"Line {line_number} must contain 4 values: "
                            f"marker_name, marker_order, longitude, latitude."
                        )

                    marker_name, marker_order_str, longitude_str, latitude_str = parts

                    try:
                        marker_order = int(marker_order_str)
                    except ValueError:
                        raise ValidationError(
                            f"Marker order must be a whole number on line {line_number}."
                        )

                    if marker_order in seen_orders:
                        raise ValidationError(
                            f"Duplicate marker order found on line {line_number}: {marker_order}."
                        )
                    seen_orders.add(marker_order)

                    try:
                        longitude = float(longitude_str)
                        latitude = float(latitude_str)
                    except ValueError:
                        raise ValidationError(
                            f"Longitude and latitude must be numeric on line {line_number}."
                        )

                    parsed_markers.append(
                        {
                            "marker_name": marker_name,
                            "marker_order": marker_order,
                            "longitude": longitude,
                            "latitude": latitude,
                        }
                    )

                if len(parsed_markers) < 3:
                    raise ValidationError("At least 3 marker rows are required.")

                parsed_markers.sort(key=lambda item: item["marker_order"])

                coords = [
                    (marker["longitude"], marker["latitude"])
                    for marker in parsed_markers
                ]

                if coords[0] != coords[-1]:
                    coords.append(coords[0])

                polygon = Polygon(coords, srid=4326)

                if not polygon.valid:
                    raise ValidationError(
                        "The marker coordinates do not form a valid polygon."
                    )

                validate_plot_overlap(polygon)

                with transaction.atomic():
                    plot = form.save(commit=False)
                    plot.polygon = polygon
                    plot.save()

                    for marker_data in parsed_markers:
                        Marker.objects.create(
                            plot=plot,
                            marker_name=marker_data["marker_name"],
                            marker_order=marker_data["marker_order"],
                            longitude=marker_data["longitude"],
                            latitude=marker_data["latitude"],
                            point=Point(
                                marker_data["longitude"],
                                marker_data["latitude"],
                                srid=4326,
                            ),
                        )

                    area_sqm, area_hectares = compute_plot_area(plot)
                    plot.area_sqm = area_sqm
                    plot.area_hectares = area_hectares
                    plot.save(update_fields=["area_sqm", "area_hectares", "updated_at"])

                messages.success(request, "Plot created from marker coordinates.")
                return redirect(f"{reverse('plots:plot_list')}?plot_id={plot.id}")

            except Exception as e:
                messages.error(request, f"Could not create plot from marker coordinates: {e}")
    else:
        form = PlotMarkerCoordinatesForm()

    return render(
        request,
        "plots/create_plot_by_marker_coordinates.html",
        {"form": form},
    )


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

                validate_plot_overlap(polygon)

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
                return redirect(f"{reverse('plots:plot_list')}?plot_id={plot.id}")

            except Exception as e:
                messages.error(request, f"Could not save drawn polygon: {e}")
    else:
        form = PlotMapForm()

    return render(request, "plots/create_plot_by_map.html", {"form": form})



def plot_list(request):
    plots = Plot.objects.filter(polygon__isnull=False).order_by("-is_active", "plot_name")

    selected_plot_id = request.GET.get("plot_id")
    selected_plot = None

    if selected_plot_id:
        selected_plot = get_object_or_404(Plot, id=selected_plot_id)
    elif plots.exists():
        selected_plot = plots.first()

    if request.method == "POST" and "split_plot" in request.POST:
        if not user_is_agent(request.user):
            messages.error(request, "You do not have permission to split plots.")
            return redirect("plots:plot_list")

        if not selected_plot:
            messages.error(request, "No plot selected for splitting.")
            return redirect("plots:plot_list")

        if not selected_plot.is_active:
            messages.error(request, "Only active plots can be split.")
            return redirect(f"{request.path}?plot_id={selected_plot.id}")

        if not selected_plot.polygon:
            messages.error(request, "Selected plot has no polygon to split.")
            return redirect(f"{request.path}?plot_id={selected_plot.id}")

        split_form = SplitPlotForm(request.POST)

        if split_form.is_valid():
            polygon_json = request.POST.get("polygon_json")

            try:
                if not polygon_json:
                    raise ValidationError("No cut polygon was drawn.")

                coords = json.loads(polygon_json)

                if len(coords) < 3:
                    raise ValidationError("The cut polygon must have at least 3 points.")

                cut_coords = []
                for point in coords:
                    longitude = float(point["lng"])
                    latitude = float(point["lat"])
                    cut_coords.append((longitude, latitude))

                if cut_coords[0] != cut_coords[-1]:
                    cut_coords.append(cut_coords[0])

                cut_polygon = Polygon(cut_coords, srid=4326)

                if not cut_polygon.valid:
                    raise ValidationError("The cut polygon is not valid.")

                cut_polygon = snap_polygon_vertices_to_parent(
                    cut_polygon,
                    selected_plot,
                    tolerance=0.0001,
                )

                validate_plot_within_parent(cut_polygon, selected_plot)
                remainder_polygon = split_plot_geometry(selected_plot, cut_polygon)

                with transaction.atomic():
                    cut_plot = split_form.save(commit=False)
                    cut_plot.parent_plot = selected_plot
                    cut_plot.polygon = cut_polygon
                    cut_plot.is_active = True
                    cut_plot.save()

                    cut_area_sqm, cut_area_hectares = compute_plot_area(cut_plot)
                    cut_plot.area_sqm = cut_area_sqm
                    cut_plot.area_hectares = cut_area_hectares
                    cut_plot.save(update_fields=["area_sqm", "area_hectares", "updated_at"])

                    extract_markers_from_polygon(cut_plot)

                    remainder_plot = Plot.objects.create(
                        plot_name=f"{selected_plot.plot_name}_R1",
                        plot_code=f"{selected_plot.plot_code}_R1" if selected_plot.plot_code else None,
                        polygon=remainder_polygon,
                        parent_plot=selected_plot,
                        is_active=True,
                    )

                    rem_area_sqm, rem_area_hectares = compute_plot_area(remainder_plot)
                    remainder_plot.area_sqm = rem_area_sqm
                    remainder_plot.area_hectares = rem_area_hectares
                    remainder_plot.save(update_fields=["area_sqm", "area_hectares", "updated_at"])

                    extract_markers_from_polygon(remainder_plot)

                    selected_plot.is_active = False
                    selected_plot.is_subdivided = True
                    selected_plot.save(update_fields=["is_active", "is_subdivided", "updated_at"])

                messages.success(
                    request,
                    f"Plot split successfully. Created '{cut_plot.plot_name}' and remainder '{remainder_plot.plot_name}'."
                )
                return redirect(f"{request.path}?plot_id={selected_plot.id}")

            except Exception as e:
                messages.error(request, f"Could not split plot: {e}")
    else:
        split_form = SplitPlotForm()

    plot_data = []
    for plot in plots:
        coords = list(plot.polygon.coords[0]) if plot.polygon else []
        plot_data.append(
            {
                "id": plot.id,
                "name": plot.plot_name,
                "code": plot.plot_code,
                "coords": coords,
                "area_sqm": plot.area_sqm,
                "area_hectares": plot.area_hectares,
                "is_active": plot.is_active,
                "is_selected": selected_plot.id == plot.id if selected_plot else False,
            }
        )

    selected_plot_coords = []
    child_plots = Plot.objects.none()

    if selected_plot:
        if selected_plot.polygon:
            selected_plot_coords = list(selected_plot.polygon.coords[0])
        child_plots = selected_plot.sub_plots.order_by("plot_name")

    total_plots_count = plots.count()
    active_plots_count = plots.filter(is_active=True).count()
    inactive_plots_count = plots.filter(is_active=False).count()
    owners_count = Owner.objects.count()

    return render(
        request,
        "plots/plot_list.html",
        {
            "plots": plots,
            "plot_data": plot_data,
            "selected_plot": selected_plot,
            "selected_plot_coords": selected_plot_coords,
            "child_plots": child_plots,
            "split_form": split_form,
            "total_plots_count": total_plots_count,
            "active_plots_count": active_plots_count,
            "inactive_plots_count": inactive_plots_count,
            "owners_count": owners_count,
            "is_agent_user": user_is_agent(request.user),
        },
    )



def owner_list(request):
    owners = Owner.objects.all().order_by("surname", "first_name", "other_name")
    return render(request, "plots/owner_list.html", {"owners": owners})


def owner_create(request):
    if request.method == "POST":
        form = OwnerForm(request.POST, request.FILES)
        if form.is_valid():
            owner = form.save()
            messages.success(request, "Owner created successfully.")
            return redirect(f"{reverse('plots:owner_list')}?owner_id={owner.id}")
    else:
        form = OwnerForm()

    return render(request, "plots/owner_create.html", {"form": form})




def plot_gallery(request, plot_id):
    plot = get_object_or_404(Plot, id=plot_id)

    front_images = plot.media_files.filter(media_type="image", media_role="front_view")
    back_images = plot.media_files.filter(media_type="image", media_role="back_view")
    left_images = plot.media_files.filter(media_type="image", media_role="left_view")
    right_images = plot.media_files.filter(media_type="image", media_role="right_view")
    other_images = plot.media_files.filter(media_type="image", media_role="other_view")
    videos = plot.media_files.filter(media_type="video", media_role="plot_video")

    polygon_coords = []
    if plot.polygon:
        polygon_coords = list(plot.polygon.coords[0])

    return render(
        request,
        "plots/plot_gallery.html",
        {
            "plot": plot,
            "polygon_coords": polygon_coords,
            "front_images": front_images,
            "back_images": back_images,
            "left_images": left_images,
            "right_images": right_images,
            "other_images": other_images,
            "videos": videos,
        },
    )





def delete_plot_media(request, plot_id, media_id):
    plot = get_object_or_404(Plot, id=plot_id)
    media = get_object_or_404(PlotMedia, id=media_id, plot=plot)

    if request.method == "POST":
        media.delete()
        messages.success(request, "Media deleted successfully.")
        return redirect("plots:plot_detail", plot_id=plot.id)

    return render(
        request,
        "plots/delete_plot_media.html",
        {
            "plot": plot,
            "media": media,
        },
    )





def buyer_create(request):
    if request.method == "POST":
        form = BuyerRegistrationForm(request.POST)
        if form.is_valid():
            full_name = form.cleaned_data["full_name"].strip()
            email = form.cleaned_data["email"].strip().lower()
            password = form.cleaned_data["password1"]

            first_name = full_name
            last_name = ""

            if " " in full_name:
                parts = full_name.split()
                first_name = parts[0]
                last_name = " ".join(parts[1:])

            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                is_active=True,
            )

            #buyer_group, _ = Group.objects.get_or_create(name="Buyer")
            #user.groups.add(buyer_group)

            messages.success(request, f"Buyer account created successfully for {email}.")
            return redirect("plots:plot_list")
    else:
        form = BuyerRegistrationForm()

    return render(
        request,
        "plots/buyer_create.html",
        {
            "form": form,
        },
    )




def buyer_register(request):
    if request.user.is_authenticated:
        return redirect("plots:plot_list")

    if request.method == "POST":
        form = BuyerRegistrationForm(request.POST)
        if form.is_valid():
            full_name = form.cleaned_data["full_name"].strip()
            email = form.cleaned_data["email"].strip().lower()
            password = form.cleaned_data["password1"]

            first_name = full_name
            last_name = ""

            if " " in full_name:
                parts = full_name.split()
                first_name = parts[0]
                last_name = " ".join(parts[1:])

            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                is_active=True,
            )

            #buyer_group, _ = Group.objects.get_or_create(name="Buyer")
            #user.groups.add(buyer_group)

            login(request, user)

            messages.success(request, "Buyer account created successfully. You are now logged in.")
            return redirect("plots:plot_list")
    else:
        form = BuyerRegistrationForm()

    return render(
        request,
        "plots/buyer_register.html",
        {
            "form": form,
        },
    )



def buyer_login(request):
    if request.user.is_authenticated:
        return redirect("plots:plot_list")

    form = BuyerLoginForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        identifier = form.cleaned_data["email"].strip()
        password = form.cleaned_data["password"]

        user = authenticate(request, username=identifier, password=password)

        if user is None and "@" in identifier:
            try:
                matched_user = User.objects.get(email__iexact=identifier)
                user = authenticate(request, username=matched_user.username, password=password)
            except User.DoesNotExist:
                user = None

        if user is not None:
            if not user.is_active:
                messages.error(request, "This account is inactive. Please contact support.")
            else:
                login(request, user)
                messages.success(request, "You have logged in successfully.")
                return redirect("plots:plot_list")
        else:
            messages.error(request, "Invalid email/username or password.")

    return render(
        request,
        "plots/buyer_login.html",
        {
            "form": form,
        },
    )


def buyer_logout(request):
    if request.user.is_authenticated:
        logout(request)
        messages.success(request, "You have logged out successfully.")
    return redirect("plots:plot_list")




#========== helper functions===

def user_is_agent(user):
    return user.is_authenticated and (
        user.is_superuser or user.groups.filter(name="Agent").exists()
    )


def user_is_registered_user(user):
    return user.is_authenticated


def user_can_view_gallery(user):
    return user.is_authenticated



#===================================================================================

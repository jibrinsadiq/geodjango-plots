
from django.contrib.gis.geos import Polygon, Point
from django.core.exceptions import ValidationError
from .models import Marker


def build_polygon_from_markers(plot):
    markers = list(plot.markers.order_by("marker_order"))

    if len(markers) < 3:
        raise ValidationError("A plot must have at least 3 markers.")

    coords = [(marker.longitude, marker.latitude) for marker in markers]

    if coords[0] != coords[-1]:
        coords.append(coords[0])

    polygon = Polygon(coords, srid=4326)

    if not polygon.valid:
        raise ValidationError("The marker coordinates do not form a valid polygon.")

    return polygon




def extract_markers_from_polygon(plot):
    if not plot.polygon:
        raise ValidationError("Plot has no polygon to extract markers from.")

    coords = list(plot.polygon.coords[0])

    # remove closing coordinate if repeated
    if len(coords) > 1 and coords[0] == coords[-1]:
        coords = coords[:-1]

    created_markers = []

    for index, (longitude, latitude) in enumerate(coords, start=1):
        marker = Marker.objects.create(
            plot=plot,
            marker_name=f"temp{index}",
            marker_order=index,
            longitude=longitude,
            latitude=latitude,
            point=Point(longitude, latitude, srid=4326),
        )
        created_markers.append(marker)

    return created_markers
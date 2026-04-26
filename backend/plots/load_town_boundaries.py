import os
from django.contrib.gis.utils import LayerMapping
from .models import TownBoundary

town_boundary_mapping = {
    "fid": "fid",
    "TOWN_NAME": "TOWN_NAME",
    "TOWN_CATEG": "TOWN_CATEG",
    "PARENT_TOW": "PARENT_TOW",
    "PARENT_T_1": "PARENT_T_1",
    "STATE": "STATE",
    "Town_rank": "Town_rank",
    "Town_cat": "Town_cat",
    "Update_Ver": "Update_Ver",
    "geom": "MULTIPOLYGON",
}

def run(strict=True, verbose=True):
    shapefile = "/app/data/town_boundaries/NG_Town_Boundaries.shp"

    lm = LayerMapping(
        TownBoundary,
        shapefile,
        town_boundary_mapping,
        transform=True,
        encoding="utf-8",
    )
    lm.save(strict=strict, verbose=verbose)
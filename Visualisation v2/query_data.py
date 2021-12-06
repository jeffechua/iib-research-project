# This module queries the previously instantiated sample data from Blazegraph
# and creates output files suitable for use with the DTVF
# ===============================================================================

import json
import os
from config import *
from jps import remote_client
from pyproj import Transformer
from polygon_deserialiser import deserialise_polygon_2d
from sparql import *
from srs import *

# Specify plotting parameters for GeoJSON features (points, polygons, extruded polygons)


def circle_props(colour):
    return {'displayName': '',
            'description': '',
            'circle-color': colour,
            'circle-stroke-width': 1,
            'circle-stroke-color': '#000000',
            'circle-stroke-opacity': 0.75,
            'circle-opacity': 0.66
            }


def fill_props(colour):
    return {'displayName': '',
            'description': '',
            'fill-color': colour,
            'fill-outline-color': '#000000',
            'fill-opacity': 0.66
            }


def extrusion_props(base, height, colour):
    return {'displayName': '',
            'description': '',
            'fill-extrusion-base': base,
            'fill-extrusion-height': height,
            'fill-extrusion-color': colour,
            'fill-extrusion-opacity': 0.66
            }


def make_feature(id, props, geometry_type, coords):
    return {
        'type': 'Feature',
        'id': id,
        'properties': props,
        'geometry': {
            'type': geometry_type,
            'coordinates': coords
        }
    }


# ===============================================================================
# Functions to Structure Retrieved Data for DTVF

theme_lookup = {'roof': 0, 'wall': 1, 'ground': 2}
colour_lookup = {'roof': '#ff0000', 'wall': '#00ff00', 'ground': '#0000ff'}

features_centroids = [[], [], []]
features_2d = [[], [], []]
features_3d = [[], [], []]
metadata_centroids = [[], [], []]
metadata_surfs = [[], [], []]

# buildings_query = autoformat(f'''
# SELECT ?gmlId ?toid ?uprn ?centroid WHERE {{
#     ?cityobject sdec:hasWgs84Centroid ?centroid;
#                 ocgl:gmlId            ?gmlId;
#                 ocgl:objectClassId    "26".
#     OPTIONAL {{ ?identifier osid:identifies ?cityObject;
#                             osid:hasValue ?toid.
#                 OPTIONAL {{ ?blpu osid:isLinkedTo ?toid;
#                                   osid:hasValue   ?uprn. }} }}
# }}
# ''')

surfaces_query = autoformat(f'''
SELECT ?gmlId ?cityObjectId ?cityObjectClassId ?theme ?centroid ?normal ?geometry (DATATYPE(?geometry) as ?structure) WHERE {{
    ?surface  ocgl:GeometryType ?geometry;
              ocgl:gmlId        ?gmlId;
              sdec:hasTheme     ?theme;
              sdec:hasWgs84Centroid ?centroid;
              sdec:hasNormal    ?normal;
              ocgl:cityObjectId ?cityObjectId.
    ?cityObjectId ocgl:objectClassId ?cityObjectClassId.
    FILTER (!isBlank(?geometry))
}}
''')
#buildings = json.loads(remote_client.execute(buildings_query))
surfaces = json.loads(remote_client.execute(surfaces_query))

id = 0

# for building in buildings:
#     coord = [float(number) for number in building['geometry'].split('#')]
#     features_building_centroids.append(
#         feature_generator(id, circle_props, 'Point', coord))
#     metadata_building_centroids.append({
#         'id': id,
#         'gmlId': building['gmlId'],
#         'toid': building.get('toid'),
#         'blpu': building.get('blpu')
#     })
#     id += 1

for surface in surfaces:
    # retrieve geometric information
    xy, z = deserialise_polygon_2d(
        surface['geometry'], surface['structure'], transformer=proj, flip_xy_out=True)
    centroid = [float(number) for number in surface['centroid'].split('#')]
    # retrieve thematic information
    theme = surface['theme']
    official_theme = theme if surface['cityObjectClassId'] == '26' else    \
                     'roof' if surface['cityObjectClassId'] == '33' else   \
                     'wall' if surface['cityObjectClassId'] == '34' else   \
                     'ground' if surface['cityObjectClassId'] == '35' else \
                     'unknown'
    layer = theme_lookup[theme]
    colour = colour_lookup[theme] if official_theme == theme else '#ffffff'
    # construct metadata and coords
    # WGS84 is officially (lat, lon), but the visualisation wants (lon, lat).
    metadata = {
        'id': id,
        'gmlId': surface['gmlId'],
        'cityObjectId': surface['cityObjectId'],
        'theme': theme,
        'officialTheme': official_theme,
        'normal': surface['normal'].split("#")
    }
    # write data
    features_2d[layer].append(make_feature(
        id, fill_props(colour), 'Polygon', xy))
    features_3d[layer].append(make_feature(
        id, extrusion_props(min(z), max(z), colour), 'Polygon', xy))
    metadata_surfs[layer].append(metadata.copy())
    id += 1
    features_centroids[layer].append(make_feature(
        id, circle_props(colour), 'Point', [centroid[1], centroid[0]]))
    metadata['id'] = id
    metadata_centroids[layer].append(metadata)
    id += 1

# Create lists for all files to write incl. respective folder and filenames
geojson = [features_centroids[0], features_centroids[1], features_centroids[2],
           features_2d[0], features_2d[1], features_2d[2],
           features_3d[0], features_3d[1], features_3d[2]]
metadata = [metadata_centroids[0], metadata_centroids[1], metadata_centroids[2],
            metadata_surfs[0], metadata_surfs[1], metadata_surfs[2],
            metadata_surfs[0], metadata_surfs[1], metadata_surfs[2]]
folder = ['2D', '2D', '2D', '2D', '2D', '2D', '3D', '3D', '3D']
filename = ['roof-centroids', 'wall-centroids', 'ground-centroids',
            'roofs', 'walls', 'grounds',
            'roofs', 'walls', 'grounds']

# Write all output files
for i in range(len(geojson)):
    # Write GeoJSON dictionaries formatted to file
    file_name = os.path.join(OUTPUT_DIR, folder[i], filename[i] + '.geojson')
    with open(file_name, 'w') as f:
        json.dump({
            'type': 'FeatureCollection',
            'features': geojson[i]
        }, f, indent=4)
    file_name = os.path.join(OUTPUT_DIR, folder[i], filename[i] + '-meta.json')
    with open(file_name, 'w') as f:
        json.dump(metadata[i], f, indent=4)

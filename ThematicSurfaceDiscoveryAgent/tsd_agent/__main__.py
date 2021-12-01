import json
from .config import *
from .jps import remote_client
from .polygon_deserialiser import deserialise_polygon_3d
from .sparql import *
import numpy as np
from math import acos, pi
from shapely.geometry import Polygon
import pyproj

# Identify srses and build transformers in anticipation

srs_query = autoformat(f'''
SELECT DISTINCT ?srs WHERE {{ ?a ocgl:srsname ?srs }}
''')

srses = json.loads(remote_client.execute(srs_query))

print(f'Identified {len(srses)} distinct srsnames.')

srs_dict = {}
for line in srses:
    srs_dict[line['srs']] = pyproj.Transformer.from_crs(line['srs'], 'EPSG:4326', always_xy=True)
srs_dict[DEFAULT_SRS] = pyproj.Transformer.from_crs(DEFAULT_SRS, 'EPSG:4326', always_xy=True)

# Query all surfaces and their relevant information

surfaces_query = autoformat(f'''
SELECT ?iri ?building ?srs ?geometry (DATATYPE(?geometry) as ?structure) WHERE {{
    ?iri  ocgl:GeometryType ?geometry;
    OPTIONAL {{ ?iri ocgl:srsname ?srs }}
    FILTER (!isBlank(?geometry))
}}
''')
surfaces = json.loads(remote_client.execute(surfaces_query))

updates = ['''
CLEAR GRAPH city:surfacedecoration|;
INSERT DATA { GRAPH city:surfacedecoration| {
''']
for surface in surfaces:
    coords = deserialise_polygon_3d(surface['geometry'], surface['structure'])
    if len(coords) < 1:
        print(f'No rings found in {surface["iri"]}. Skipping.')
        continue
    if len(coords[0]) < 4:
        print(f'Less than 4 vertices in {surface["iri"]}. Skipping.')
        continue
    exterior = coords[0]
    # determine theme
    d1 = np.array(exterior[0]) - np.array(exterior[1])
    d2 = np.array(exterior[1]) - np.array(exterior[2])
    cross = np.cross(d1, d2)
    axis = cross/np.linalg.norm(cross)
    if abs(acos(np.clip(np.dot(axis, [0, 0, 1]), -1.0, 1.0)) - pi/2) < 0.01:
        theme = 'wall'
    else:
        # windedness
        sum = 0
        for i in range(len(exterior)-1):
            sum += (exterior[i+1][0] - exterior[i][0]) * \
                (exterior[i+1][1] + exterior[i][1])
        theme = 'roof' if sum > 0 else 'ground'
    # determine centroid
    poly = Polygon(exterior, holes=coords[1:])
    proj = srs_dict[surface['srs'] if 'srs' in surface else DEFAULT_SRS]
    centroid = poly.centroid
    x, y = proj.transform(centroid.x, centroid.y)
    updates.append(f'<{surface["iri"]}> sdec:hasTheme "{theme}";' +
                   f' sdec:hasWgs84Centroid "{x}#{y}". ')

updates.append('} }')
update = autoformat('\n'.join(updates))
remote_client.executeUpdate(update)

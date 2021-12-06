import json
from .config import *
from .jps import remote_client
from .polygon_deserialiser import deserialise_polygon_3d
from .sparql import *
from .srs import *
from math import sqrt
from shapely.geometry import Polygon

# helper function

def vector_area(coords, transformer):
    # Newell's algorithm
    xx = [coord[0] for coord in coords]
    yy = [coord[1] for coord in coords]
    zz = [coord[2] for coord in coords]
    transformer.transform(xx, yy, inplace=True)
    x, y, z = 0, 0, 0
    for i in range(len(coords)-1):
        x += (zz[i+1]+zz[i])*(yy[i+1]-yy[i])
        y += (xx[i+1]+xx[i])*(zz[i+1]-zz[i])
        z += (yy[i+1]+yy[i])*(xx[i+1]-xx[i])
    magnitude = sqrt(x*x+y*y+z*z) or 1
    return (x, y, z), (x/magnitude, y/magnitude, z/magnitude), magnitude

# Query all surfaces and assign centroid and tentative themes


surfaces = json.loads(remote_client.execute(
    autoformat(f'''
SELECT ?iri ?building ?srs ?geometry (DATATYPE(?geometry) as ?structure) WHERE {{
    ?iri  ocgl:GeometryType ?geometry;
    OPTIONAL {{ ?iri ocgl:srsname ?srs }}
    FILTER (!isBlank(?geometry))
}}
''')
))
updates = ['''
CLEAR GRAPH city:surfacedecoration|;
INSERT DATA { GRAPH city:surfacedecoration| {
''']
for surface in surfaces:
    rings = deserialise_polygon_3d(surface['geometry'], surface['structure'])
    if len(rings) < 1:
        print(f'No rings found in {surface["iri"]}. Skipping.')
        continue
    if len(rings[0]) < 4:
        print(f'Less than 4 vertices in {surface["iri"]}. Skipping.')
        continue
    exterior = rings[0]
    # determine normal (in EPSG:25833) and thus theme
    v_area, normal, area = vector_area(exterior, proj_metric)
    theme = 'wall' if abs(normal[2]) < 0.01 else \
            'roof' if normal[2] > 0 else 'ground'
    # determine centroid and project to EPSG:4326
    native_centroid = Polygon(exterior, holes=rings[1:]).centroid
    x, y = proj.transform(native_centroid.x, native_centroid.y)
    z = Polygon([(coord[2], coord[0], coord[1]) for coord in exterior],
                holes=[[(coord[2], coord[0], coord[1]) for coord in ring] for ring in rings[1:]]).centroid.x
    updates.append(f'''
    <{surface["iri"]}> sdec:hasTheme         "{theme}";
                       sdec:hasWgs84Centroid "{x}#{y}#{z}";
                       sdec:hasNormal        "{normal[0]}#{normal[1]}#{normal[2]}";
                       sdec:hasArea          "{area}".
    ''')

updates.append('} }')
update = autoformat('\n'.join(updates))
remote_client.executeUpdate(update)

print(f'Tentative decoration complete: {len(surfaces)} surfaces decorated.')

# Requery and analyse guess winding order from whether roofs are above grounds
surfaces = json.loads(remote_client.execute(autoformat(f'''
SELECT * WHERE {{
    {{
        SELECT ?buildingRoot ?theme ?centroid ?area WHERE {{
            ?surface    sdec:hasTheme         ?theme;
                        sdec:hasWgs84Centroid ?centroid;
                        sdec:hasArea          ?area;
                        ocgl:cityObjectId     ?cityObject.
            ?cityObject ocgl:buildingId       ?building.
            ?building   ocgl:buildingRootId   ?buildingRoot.
        }}
    }}
    UNION
    {{
        SELECT ?buildingRoot ?theme ?centroid WHERE {{
            ?surface    sdec:hasTheme         ?theme;
                        sdec:hasWgs84Centroid ?centroid;
                        sdec:hasArea          ?area;
                        ocgl:cityObjectId     ?cityObject.
            ?cityObject ocgl:buildingRootId ?buildingRoot.
        }}
    }}
}} ORDER BY ?buildingRoot
''')))

current_building = surfaces[0]['buildingRoot']
count = [0, 0, 0]
total_z = [0, 0, 0]

theme_lookup = {'roof': 0, 'wall': 1, 'ground': 2}
ROOF, WALL, GROUND = 0, 1, 2

correct, incorrect, walls_above, walls_below = 0, 0, 0, 0


def close_building():
    global count, total_z, correct, incorrect, walls_above, walls_below, ROOF, WALL, GROUND
    avg_z = [total_z[i]/(count[i] or 1) for i in range(3)]
    if avg_z[ROOF] > avg_z[GROUND]:
        correct += 1
    else:
        incorrect += 1
    if avg_z[WALL] > avg_z[GROUND] and avg_z[WALL] > avg_z[ROOF]:
        walls_above += 1
    elif avg_z[WALL] < avg_z[GROUND] and avg_z[WALL] < avg_z[ROOF]:
        walls_below += 1
    total_z = [0, 0, 0]
    count = [0, 0, 0]


for surface in surfaces:
    if surface['buildingRoot'] != current_building:
        close_building()
        current_building = surface['buildingRoot']
    theme_index = theme_lookup[surface['theme']]
    total_z[theme_index] += float(surface['centroid'].split('#')[2])
    count[theme_index] += 1
close_building()

total_count = correct+incorrect
correctness = correct/total_count
a_weirdness = walls_above/total_count
b_weirdness = walls_below/total_count
is_inverted = correctness < 0.5
confidence = correctness-a_weirdness-b_weirdness
confidence = 1 - confidence if is_inverted else confidence

print(f'''
Analysis complete:
    {correct} of {total_count} buildings ({correctness:>.1%}) have roofs above grounds.
    {walls_above} of {total_count} of buildings ({a_weirdness:>.1%}) have walls above roofs and grounds.
    {walls_below} of {total_count} of buildings ({b_weirdness:>.1%}) have walls below roofs and grounds.
    Winding orders are {'INVERTED' if correctness<0.5 else 'NOT INVERTED'} ({confidence:.1%} confidence).
''')

if is_inverted:
    # invert roof and ground themes
    remote_client.executeUpdate(autoformat(f'''
    INSERT {{ GRAPH city:surfacedecoration| {{ ?surface sdec:hasThemeTemp "roof"   }} }}
    WHERE  {{ GRAPH city:surfacedecoration| {{ ?surface sdec:hasTheme     "ground" }} }};
    DELETE WHERE  {{ GRAPH city:surfacedecoration| {{ ?surface sdec:hasTheme "ground" }} }};
    INSERT {{ GRAPH city:surfacedecoration| {{ ?surface sdec:hasTheme "ground" }} }}
    WHERE  {{ GRAPH city:surfacedecoration| {{ ?surface sdec:hasTheme "roof"   }} }};
    DELETE WHERE  {{ GRAPH city:surfacedecoration| {{ ?surface sdec:hasTheme "roof" }} }};
    INSERT {{ GRAPH city:surfacedecoration| {{ ?surface sdec:hasTheme     "roof"   }} }}
    WHERE  {{ GRAPH city:surfacedecoration| {{ ?surface sdec:hasThemeTemp "roof" }} }};
    DELETE WHERE  {{ GRAPH city:surfacedecoration| {{ ?surface sdec:hasThemeTemp ?theme }} }};
    '''))
    print('Inverted roof and ground themes.')
    # invert normals
    normals = json.loads(remote_client.execute(autoformat(f'''
    SELECT * WHERE {{ GRAPH city:surfacedecoration| {{ ?surface sdec:hasNormal ?normal }} }}
    ''')))
    updates = ['''
    DELETE WHERE { GRAPH city:surfacedecoration| { ?surface sdec:hasNormal ?normal } };
    INSERT DATA { GRAPH city:surfacedecoration| {
    ''']
    for row in normals:
        normal = [-float(num) for num in row['normal'].split('#')]
        updates.append(f'<{row["surface"]}> sdec:hasNormal "{normal[0]}#{normal[1]}#{normal[2]}".')
    updates.append('} }')
    remote_client.executeUpdate(autoformat('\n'.join(updates)))
    print('Inverted normals.')
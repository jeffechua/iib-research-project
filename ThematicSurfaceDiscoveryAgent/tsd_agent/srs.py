import json
from .config import *
from .jps import remote_client
from .sparql import *
from pyproj import Transformer

__all__ = ['srs', 'proj', 'proj_metric']

srs = json.loads(remote_client.execute(autoformat(
    'SELECT DISTINCT ?srs WHERE { ?a ocgl:srsname ?srs }')))
if len(srs) == 0:
    srs = input('Coordinate system not found. Please specify: ')
    if input('Save? (y/N): ') == 'y':
        remote_client.executeUpdate(f'''
        PREFIX ocgl: <http://www.theworldavatar.com/ontology/ontocitygml/citieskg/OntoCityGML.owl#> 
        INSERT DATA {{
            <{CITYDB_PREFIX}> ocgl:srid 1 .
        }};
        INSERT DATA {{
            <{CITYDB_PREFIX}> ocgl:srsname "{srs}" .
        }};
        ''')
        print(f'Successfully saved coordinate system: {srs}.')
else:
    srs = srs[0]['srs']
    print(f'Identified coordinate system: {srs}.')
proj = Transformer.from_crs(srs, 'EPSG:4326')
proj_metric = Transformer.from_crs(srs, 'EPSG:25833')

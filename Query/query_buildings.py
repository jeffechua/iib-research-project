from SPARQLWrapper import SPARQLWrapper, JSON
import pyproj
import json

# Specify (local) Blazegraph properties
server = "localhost"
port = "9999"
namespace = "churchill"

# Specify output coordinate reference system (CRS)
# Our Mapbox plotting framework uses EPSG:4326 (https://epsg.io/4326)
target_crs = 'urn:ogc:def:crs:EPSG::4326'

# Define PREFIXES for SPARQL queries (WITHOUT trailing '<' and '>')
PREFIXES = {
    'ocgl': 'http://www.theworldavatar.com/ontology/ontocitygml/citieskg/OntoCityGML.owl#',
    'xsd': 'http://www.w3.org/2001/XMLSchema#'
}


def create_sparql_prefix(abbreviation):
    """
        Constructs proper SPARQL Prefix String for given namespace abbreviation.

        Arguments:
            abbreviation - namespace abbreviation to construct SPARQL PREFIX string for.

        Returns:
            SPARQL query prefix string in the form "PREFIX ns: <full IRI>".
    """

    # Define global scope for global variables
    global PREFIXES

    # Raise key error if given namespace abbreviation has not been specified
    if abbreviation not in PREFIXES.keys():
        raise KeyError('Prefix: "' + abbreviation + '" has not been specified')

    # Get full IRI from pre-specified prefixes dictionary
    iri = PREFIXES[abbreviation]

    if not iri.startswith('<'):
        iri = '<' + iri
    if not iri.endswith('>'):
        iri = iri + '>'

    return 'PREFIX ' + abbreviation + ': ' + iri + ' '


def get_all_buildings():
    """
        Create SPARQL query to retrieve ALL buildings and associated (surface) geometries

        Returns:
            SPARQL query to pass to Blazegraph
    """

    # Construct query
    query = create_sparql_prefix('ocgl') + \
        create_sparql_prefix('xsd') + \
        '''SELECT ?surf ?bldg ?geom \
               WHERE { ?surf ocgl:cityObjectId ?bldg ; \
       		                 ocgl:GeometryType ?geom .       
                       FILTER (!isBlank(?geom)) }'''

    return query


def get_crs():
    """
        Create SPARQL query to retrieve coordinate reference system of triple store

        Returns:
            SPARQL query to pass to Blazegraph
    """

    # Construct query
    query = create_sparql_prefix('ocgl') + \
        '''SELECT ?crs \
               WHERE { ?s ocgl:srsname ?crs . }'''

    return query


def execute_query(query, query_endpoint):
    '''
        Executes provided SPARQL query and returns results in JSON format

        Arguments:
            query - SPARQL query to execute.
            query_endpoint - SPARQl endpoint to execute query on.

        Returns:
            SPARQL query results in JSON format.
    '''

    # Initialise SPARQL wrapper and set endpoint and return format
    sparql = SPARQLWrapper(query_endpoint)
    sparql.setReturnFormat(JSON)

    # Set query and execute
    sparql.setQuery(query)
    results = sparql.query().convert()

    return results


def get_coordinates(polygon_data, input_crs, target_crs):
    '''
        Extracts and transforms polygon coordinates as retrieved from Blazegraph
        to suit GeoJSON polygon requirements (and target CRS)

        Arguments:
            polygon_data - polygon data as returned from Blazegraph
            input_crs - CRS of input data (as pyproj CRS object)
            target_crs - CRS of output data (as pyproj CRS object)

        Returns:
            List of polygon coordinates as required for GeoJSON objects
            Maximum height of polygon surface
    '''

    # Initialise CRS transformer
    proj = pyproj.Transformer.from_crs(input_crs, target_crs, always_xy=True)

    # Initialise output and input coordinate collections
    coordinates = []
    coordinate_str = polygon_data.split("#")
    coordinate_str = [float(c) for c in coordinate_str]

    # If all input coordinates have proper (X,Y,Z) values ...
    if len(coordinate_str) % 3 == 0:

        # Initialise maximum height of polygon
        zmax = 0.0

        # Iterate through all polygon points
        nodes = int(len(coordinate_str) / 3)
        for i in range(nodes):
            node = i * 3
            # Transform (x,y) values and append (x,y,z) to output list
            x, y = proj.transform(
                coordinate_str[node], coordinate_str[node + 1])
            z = coordinate_str[node + 2]
            coordinates.append([x, y])

            # Update max height
            if z > zmax:
                zmax = z

        # Check if first and last polygon vertices are equivalent and fix if necessary
        if coordinates[0] != coordinates[-1]:
            print('Surface polygon did not close properly! Geometry has been fixed.')
            coordinates.append(coordinates[0])

    # ... otherwise print error
    else:
        print('Erroneous polygon coordinates:', coordinate_str)

    return coordinates, zmax


if __name__ == '__main__':

    # Construct full SPARQL endpoint URL
    query_endpoint = "http://" + server + ':' + port + \
        '/blazegraph/namespace/' + namespace + "/sparql"

    # Retrieve SPARQL results from Blazegraph
    kg_buildings = execute_query(get_all_buildings(), query_endpoint)
    kg_crs = execute_query(get_crs(), query_endpoint)

    # Unpack CRS SPARQL result to extract coordinate reference system
    crs_in = kg_crs['results']['bindings'][0][kg_crs['head']
                                              ['vars'][0]]['value']
    crs_in = pyproj.CRS.from_string(crs_in)
    crs_out = pyproj.CRS.from_string(target_crs)

    # Start GeoJSON output file
    output = {
        'type': 'FeatureCollection',
        'features': []
    }

    # Iterate through all geospatial features
    # Unpack buildings SPARQL results into dictionary in format {surface_IRI: [building_IRI, polygon_data]}
    for surface in kg_buildings["results"]["bindings"]:

        coords, zmax = get_coordinates(
            surface["geom"]["value"], crs_in, crs_out)

        # Specify feature properties to consider (beyond coordinates)
        props = {
            "name": surface['bldg']['value'],
            'fill-extrusion-height': round(zmax, 3),
            "type": "multipolygon",
        }

        feature = {
            'type': 'Feature',
            'id': len(output['features']),
            'properties': props,
            'geometry': {
                'coordinates': [coords],
                'type': 'Polygon'
            }
        }

        output['features'].append(feature)

    # Write output to file
    with open('../Visualisation/dtvf_visualisation/queried_data/fixed/buildings.geojson', 'w') as f:
        json.dump(output, f, indent=4)

from flask import Blueprint, jsonify
from ..sparql import *
from ..jps import remote_client
from ..common_queries import query_identifier_links, query_identifier_properties

blueprint = Blueprint('query', __name__)

@blueprint.route('/', methods=['GET'])
def query_graph_info():
    return  '''
    Returns the properties of  a JSON object with fields:
        - `id`: same as provided.
        - `id_type`: same as provided, but converted to lowercase.
        - `feature_type`: the feature type as a string, or null if the identifier is not instantiated in the graph.
        - `identificand`: an IRI string pointing to the cityobject this identifier identifies, or null.
        - `rank`: the rank of the identified object, or null.
    '''

# Define a route for API requests
@blueprint.route('/<id_type>/<id>', methods=['GET'])
def query_graph(id_type, id):
    '''
    Returns the results from internal functions query_identifier_properties and
    query_identifer_links. Response is a JSON object with fields:
        - `id`: same as provided.
        - `id_type`: same as provided, but converted to lowercase.
        - `feature_type`: the feature type as a string, or null if the identifier is not instantiated in the graph.
        - `identificand`: an IRI string pointing to the cityobject this identifier identifies, or null.
        - `rank`: the rank of the identified object, or null.
        - `links`: a list of 0 or more dictionaries, each of which contains keys (values guaranteed non-None):
            - `counterparty`: IRI string to the linked identifier.
            - `featureType`: the feature type of the linked identifier.
            - `identifierType`: the identifier type of the linked identifier.
            - `value`: the value of the linked identifier.
            - `rank`: the rank of the linked identifier.
    '''
    id_type = id_type.lower()
    exists, feature_type, rank, identificand = query_identifier_properties(id_type, id)
    links = query_identifier_links(id_type, id)
    return jsonify({
        'id': id,
        'id_type': id_type,
        'feature_type': feature_type,
        'rank': rank,
        'identificand': identificand,
        'linked_identifiers': links
    })

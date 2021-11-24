import requests
import json
from .sparql import *
from .jps import remote_client
from .configs import OSAPI_KEY

def query_identifier_properties(id_type, id):
    '''
    Internal utility function for getting *non-link* properties of an identifier. Returns three values, respectively:
        - `exists`: whether the provided identifier is present (in valid form) in the KG.
        - `feature_type`: the type of the feature if exists==True, else None.
        - `identificand`: the cityobject identified by the identifier if it exists, else None.

    Return modes:
        - `False`, `None`, `None`: identifier not in graph.
        - `True`, `<string>`, `None`: identifier in graph, but has no identificand.
        - `True`, `<string>`, `<IRI string>`: identifier in graph and has identificand.
    '''
    query = autoformat(f'''
    SELECT * WHERE {{
        GRAPH city:identifiers|
        {{ city:{id_type}|{id}|  osid:hasFeatureType       ?featureType  ;
                                 osid:hasIdentifierType    "{id_type}"   ;
                                 osid:hasValue             "{id}"        ;
                                 osid:hasRank              ?rank         ;
        OPTIONAL {{ city:{id_type}|{id}| osid:identifies ?identificand }} }}
    }}
    ''')
    response = json.loads(remote_client.execute(query))
    if len(response) != 1:
        return False, None, None
    else:
        return True, response[0]['featureType'], response[0]['rank'], response[0].get('identificand')


def query_identifier_links(id_type, id):
    '''
    Internal utility function for getting linked identifiers of an identifier.
    Returns a list of 0 or more dictionaries, each of which contains keys:
        - `counterparty`: IRI string to the linked identifier.
        - `featureType`: the feature type of the linked identifier.
        - `identifierType`: the identifier type of the linked identifier.
        - `value`: the value of the linked identifier.
            
    Values are guaranteed to be non-null.
    '''
    # Query KG for linked identifiers, which may return 0 or more results
    query = autoformat(f'''
    SELECT * WHERE {{
        GRAPH city:identifiers|
        {{ city:{id_type}|{id}|  osid:isLinkedTo           ?counterparty     .
           ?counterparty         osid:hasFeatureType       ?featureType      ;
                                 osid:hasIdentifierType    ?identiferType    ;
                                 osid:hasValue             ?value            ;
                                 osid:hasRank              ?rank             }}
    }}
    ''')
    return json.loads(remote_client.execute(query))


def predict_rank(feature_type):
    if feature_type == 'street' or feature_type == 'road':
        return 2
    elif feature_type == 'roadlink':
        return 1
    else:
        return 0

def query_osli(id):
    '''
    Queries the OS Linked Identifiers API for linked identifiers as well as the feature type and
    identifier type of the queried identifier. The structure of the return values is:
        - list of dictionaries containing the following keys (values guaranteed to be non-None):
            - `id_type`: the identifier type of the linked identifier.
            - `id`: the value of the linked identifier.
            - `feature_type`: the feature type of the linked identifier.
            - `rank`: the rank of the linked identifier.
        - feature type of the queried identifier (string)
        - identifier type of the queried identifier (string)
        - rank of the queried identifier (int): 0, 1 or 2.

    Return modes:
        - `None`, `None`, `None`, `None`: invalid identifier.
        - `[]`, `None`, `None`, `None`: valid identifier, but the Linked Identifiers API has no data on it.
        - `[0 or more items]`, `<string>`, `<string>`, `<int>`: valid identifier and Linked Identifiers has data on it.
    '''
    res = requests.get('https://api.os.uk/search/links/v1/identifiers/' + id, {'key': OSAPI_KEY}).json()
    # check for errors
    links = []
    if 'message' in res:
        if res['message'] == "Identifier not found":
            return [], None, None, None
        elif res['message'] == 'Identifier is not valid':
            return None, None, None, None
    else:
        if len(res['linkedIdentifiers']) != 1:
            raise LookupError(f'{len(res["linkedIdentifiers"])} identifiers found with name {id}')
        res = res['linkedIdentifiers'][0]
        feature_type = res['linkedIdentifier']['featureType'].lower()
        identifier_type = res['linkedIdentifier']['identifierType'].lower()
        rank = predict_rank(feature_type)
        for correl in res['correlations']:
            counter_id_type = correl['correlatedIdentifierType'].lower()
            counter_feature_type = correl['correlatedFeatureType'].lower()
            counter_rank = predict_rank(counter_feature_type)
            if rank != 0 and counter_feature_type == 'topographicarea': continue
            if counter_id_type == 'guid': continue
            for result in correl['correlatedIdentifiers']:
                links.append({
                    'id_type': counter_id_type,
                    'id': result['identifier'],
                    'feature_type': counter_feature_type,
                    'rank': counter_rank
                })
        return links, feature_type, identifier_type, rank


def instantiation_update_string(id_type, id, feature_type, rank):
    '''
    Returns a SPARQL query string which instantiates the identifier as specified in the knowledge graph.

    If these properties already existed, the query overwrites, not duplicates them; this operation is idempotent.
    '''
    return f'''
    DELETE WHERE {{ GRAPH city:identifiers| {{ city:{id_type}|{id}| osid:hasFeatureType      ?a }} }};
    DELETE WHERE {{ GRAPH city:identifiers| {{ city:{id_type}|{id}| osid:hasIdentifierType   ?a }} }};
    DELETE WHERE {{ GRAPH city:identifiers| {{ city:{id_type}|{id}| osid:hasValue ?a }} }};
    DELETE WHERE {{ GRAPH city:identifiers| {{ city:{id_type}|{id}| osid:hasRank ?a }} }};
    DELETE WHERE {{ GRAPH city:identifiers| {{ city:{id_type}|{id}| rdf:type ?a }} }};
    INSERT DATA {{
        GRAPH city:identifiers|
        {{ city:{id_type}|{id}| osid:hasFeatureType       "{feature_type}"  ;
                                osid:hasIdentifierType    "{id_type}"       ;
                                osid:hasValue             "{id}"            ;
                                osid:hasRank             "{rank}"            ;
                                rdf:type                  osid:PersistentIdentifier }}
    }};'''

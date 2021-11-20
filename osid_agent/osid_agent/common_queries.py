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
        {{ city:{id_type}|{id}|  ph:featureType       ?featureType  ;
                                 ph:identifierType    "{id_type}"   ;
                                 ph:identifierString  "{id}"        .
        OPTIONAL {{ city:{id_type}|{id}| ph:identifies ?identificand }} }}
    }}
    ''')
    response = json.loads(remote_client.execute(query))
    if len(response) != 1:
        return False, None, None
    else:
        return True, response[0]['featureType'], response[0].get('identificand')


def query_identifier_links(id_type, id):
    '''
    Internal utility function for getting linked identifiers of an identifier.
    Returns a list of 0 or more dictionaries, each of which contains keys:
        - `counterparty`: IRI string to the linked identifier.
        - `featureType`: the feature type of the linked identifier.
        - `identifierType`: the identifier type of the linked identifier.
        - `identifierString`: the value of the linked identifier.
            
    Values are guaranteed to be non-null.
    '''
    # Query KG for linked identifiers, which may return 0 or more results
    links_query = autoformat(f'''
    SELECT * WHERE {{
        GRAPH city:identifiers|
        {{ city:{id_type}|{id}|  ph:linkedTo          ?counterparty     .
           ?counterparty         ph:featureType       ?featureType      ;
                                 ph:identifierType    ?identiferType    ;
                                 ph:identifierString  ?identifierString }}
    }};
    ''')
    return json.loads(remote_client.execute(links_query))


def query_osli(id):
    '''
    Queries the OS Linked Identifiers API for linked identifiers as well as the feature type and
    identifier type of the queried identifier. The structure of the return values is:
        - list of dictionaries containing the following keys (values guaranteed to be non-None):
            - `id_type`: the identifier type of the linked identifier.
            - `id`: the value of the linked identifier.
            - `feature_type`: the feature type of the linked identifier.
        - feature type of the queried identifier (string)
        - identifier type of the queried identifier (string)

    Return modes:
        - `None`, `None`, `None`: invalid identifier.
        - `[]`, `None`, `None`: valid identifier, but the Linked Identifiers API has no data on it.
        - `[0 or more items]`, `<string>`, `<string>`: valid identifier and Linked Identifiers has data on it.
    '''
    res = requests.get('https://api.os.uk/search/links/v1/identifiers/' + id, {'key': OSAPI_KEY}).json()
    # check for errors
    links = []
    if 'message' in res:
        feature_type = None
        identifier_type = None
        if res['message'] == "Identifier not found":
            pass
        elif res['message'] == 'Identifier is not valid':
            return None, None, None
    else:
        if len(res['linkedIdentifiers']) != 1:
            raise LookupError(f'{len(res["linkedIdentifiers"])} identifiers found with name {id}')
        res = res['linkedIdentifiers'][0]
        feature_type = res['linkedIdentifier']['featureType'].lower()
        identifier_type = res['linkedIdentifier']['identifierType'].lower()
        for correl in res['correlations']:
            counter_id_type = correl['correlatedIdentifierType'].lower()
            counter_feature_type = correl['correlatedFeatureType'].lower()
            if counter_id_type == 'guid': continue
            for id in correl['correlatedIdentifiers']:
                links.append({
                    'id_type': counter_id_type,
                    'id': id['identifier'],
                    'feature_type': counter_feature_type
                })
    return links, feature_type, identifier_type


def instantiation_update_string(id_type, id, feature_type):
    '''
    Returns a SPARQL query string which instantiates the identifier as specified in the knowledge graph.

    If these properties already existed, the query overwrites, not duplicates them; this operation is idempotent.
    '''
    return f'''
    DELETE WHERE {{ GRAPH city:identifiers| {{ city:{id_type}|{id}| ph:featureType      ?a }} }};
    DELETE WHERE {{ GRAPH city:identifiers| {{ city:{id_type}|{id}| ph:identifierType   ?a }} }};
    DELETE WHERE {{ GRAPH city:identifiers| {{ city:{id_type}|{id}| ph:identifierString ?a }} }};
    INSERT DATA {{
        GRAPH city:identifiers|
        {{ city:{id_type}|{id}| ph:featureType       "{feature_type}"  ;
                                ph:identifierType    "{id_type}"       ;
                                ph:identifierString  "{id}"            }}
    }};'''

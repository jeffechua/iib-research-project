from flask import Blueprint, jsonify
import json
from sys import stdout
from osid_agent.endpoints.bind import bind_update_string
from ..sparql import *
from ..jps import remote_client
from ..common_queries import instantiation_update_string, query_osli
from .bind import bind_update_string

blueprint = Blueprint('os', __name__)

@blueprint.route('/query', methods=['GET'])
def query_os_info():
    return '''
    Queries the OS Linked Identifiers API and returns the results in a JSON object with elements:
        - `id`: same as provided.
        - `id_type`: feature type of the queried identifier (string)
        - `feature_type`: identifier type of the queried identifier (string)
        - `linked_identifiers`: list of dictionaries containing the following keys (values guaranteed to be non-None):
            - `id_type`: the identifier type of the linked identifier.
            - `id`: the value of the linked identifier.
            - `feature_type`: the feature type of the linked identifier.
        
    Three possible return modes:
        - `id_type = null`, `feature_type = null`, `linked_identifiers = null`: invalid identifier.
        - `id_type = null`, `feature_type = null`, `linked_identifiers = []`: valid identifier, but the Linked Identifiers API has no data on it.
        - `id_type = <string>`, `feature_type = <string>`, `linked_identifiers = [0 or more items]`: valid identifier and Linked Identifiers has data on it.
    '''

@blueprint.route('/query/<id>', methods=['GET'])
def query_os(id):
    '''
    Queries the OS Linked Identifiers API and returns the results in a JSON object with elements:
        - `id`: same as provided.
        - `id_type`: feature type of the queried identifier (string)
        - `feature_type`: identifier type of the queried identifier (string)
        - `linked_identifiers`: list of dictionaries containing the following keys (values guaranteed to be non-None):
            - `id_type`: the identifier type of the linked identifier.
            - `id`: the value of the linked identifier.
            - `feature_type`: the feature type of the linked identifier.
        
    Three possible return modes:
        - `id_type = null`, `feature_type = null`, `linked_identifiers = null`: invalid identifier.
        - `id_type = null`, `feature_type = null`, `linked_identifiers = []`: valid identifier, but the Linked Identifiers API has no data on it.
        - `id_type = <string>`, `feature_type = <string>`, `linked_identifiers = [0 or more items]`: valid identifier and Linked Identifiers has data on it.
    '''
    links, feature_type, id_type = query_osli(id)
    return jsonify({
        'id': id,
        'id_type': id_type,
        'feature_type': feature_type,
        'linked_identifiers': links
    })


@blueprint.route('/pull', methods=['GET'])
def pull_from_os_info():
    return ''''
    Imports links to the identifier from the OS Linked Identifiers API, erasing existing links to the identifier.
    Also instantiates the queried identifier and any linked identifiers if present in Linked Identifiers API.
    As instantiation is idempotent, this will not create duplicate instances, but it will overwrite incorrect properties
    if they existed before. Response describes success or failure, and the number of imported links if successful.
    '''


@blueprint.route('/pull/<id_type>/<id>', methods=['PUSH', 'GET'])
def pull_from_os(id_type, id, instantiate=True, update_out=None, links_out=None):
    ''''
    Imports links to the identifier from the OS Linked Identifiers API, erasing existing links to the identifier.

    `instantiate` should either be `True`, `False`, or a set.
    - `True`: instantiate queried identifier and any linked identifiers.
    - `False`: do not instantiate any identifiers.
    - `set object`: for each identifier, check if it is in the set; only if not, instantiate it and add identifier to set.
    Also instantiates the queried identifier and any linked identifiers if `instantiate=true` and present in Linked
    Identifiers API. This is the default, and cannot be modified when calling this via HTTP request.
    As instantiation is idempotent, this will not create duplicate instances, but it will overwrite incorrect properties
    if they existed before.
    
    Return value is a text string describes success or failure, as well as number of imported links if successful.

    If `links_out` is provided, the links retrieved from OSLI are added to it.

    If `update_out` is provided, the update_lines is extended to it instead of executed.
    '''

    id_type = id_type.lower()
    update_lines = []

    # Query data on the identifier from the OS Linked Identifiers API
    os_links, os_feature_type, os_id_type, os_rank = query_osli(id)
    if os_links == None:
        return f'{id_type}:{id}:unknown: Invalid identifier.'
    if os_feature_type == None:
        return f'{id_type}:{id}:unknown: OSLI has no data on this identifier.'
    if os_id_type != id_type:
        return f'{id_type}:{id}:{os_feature_type} OSLI believes is a {os_id_type}, not a {id_type}; aborting.'
    
    original_length = len(os_links)
    os_links = list(filter(lambda link: link['rank'] >= os_rank, os_links))

    # If the caller wants to know the links, give them to them
    if links_out != None:
        links_out.update([f'{link["id_type"]}:{link["id"]}:{link["feature_type"]}' for link in os_links])

    # Instantiate identifiers if instantiate=true
    if instantiate == True:
        update_lines.append(instantiation_update_string(id_type, id, os_feature_type, os_rank))
        for link in os_links:
            update_lines.append(instantiation_update_string(link['id_type'], link['id'], link['feature_type'], link['rank']))

    # If 'instantiate' is a set, instantiate identifiers only if they aren't in it, and then add them to it
    elif isinstance(instantiate, set):
        if f'{id_type}:{id}:{os_feature_type}' not in instantiate:
            update_lines.append(instantiation_update_string(id_type, id, os_feature_type, os_rank))
            instantiate.add(f'{id_type}:{id}:{os_feature_type}')
        for link in os_links:
            if f'{link["id_type"]}:{link["id"]}:{link["feature_type"]}' not in instantiate:
                update_lines.append(instantiation_update_string(link["id_type"], link["id"], link["feature_type"], link['rank']))
                instantiate.add(f'{link["id_type"]}:{link["id"]}:{link["feature_type"]}')

    # Import links (removing all old links)
    self_iri = f'city:{id_type}|{id}|'
    update_lines.append(f'''
    DELETE {{ {self_iri}  osid:isLinkedTo  ?linked.
              ?linked     osid:isLinkedTo  {self_iri}.}}
    WHERE  {{ GRAPH city:identifiers| {{ ?linked osid:isLinkedTo {self_iri};
                                                 osid:hasRank ?rank. FILTER(?rank >= "{os_rank}") }}}};
    DELETE WHERE {{ GRAPH city:identifiers| {{ {self_iri}  osid:linksLastRetrieved ?datetime; osid:linksRetrievedFrom ?source.  }}}};
    INSERT {{ GRAPH city:identifiers| {{ {self_iri} osid:linksLastRetrieved ?now; osid:linksRetrievedFrom "api". }}}}
    WHERE {{ SELECT ?now WHERE {{ BIND(xsd:dateTime(NOW()) as ?now)}} }};
    INSERT DATA {{ GRAPH city:identifiers| {{
        {self_iri} osid:linksRetrievedFrom "api".
    ''')
    for link in os_links:
        cpty_iri = f'city:{link["id_type"]}|{link["id"]}|'
        update_lines.append(f'{self_iri} osid:isLinkedTo {cpty_iri}.')
        update_lines.append(f'{cpty_iri} osid:isLinkedTo {self_iri}.')
    update_lines.append('} };')

    if update_out == None:
        remote_client.executeUpdate(autoformat('\n'.join(update_lines)))
    else:
        update_out.append('\n'.join(update_lines))

    return f"{id_type}:{id}:{os_feature_type} {len(os_links)}/{original_length} links imported successfully."


@blueprint.route('/pull-all/', methods=['PUSH', 'GET'])
@blueprint.route('/pull-all/<count>', methods=['PUSH', 'GET'])
def pull_all_from_os(count = -1):
    '''
    Calls pull_from_os on every building in the knowledge graph,
    defined as IRIs with a reflexive ocgl:id property in the city:building graph.
    '''

    response_lines = []
    buildings_query = autoformat(f'''
    SELECT ?building WHERE {{
        GRAPH city:building|
        {{ ?building ocgl:id ?building }}
    }} {'' if count == -1 else f'LIMIT {count}'}
    ''')
    buildings = json.loads(remote_client.execute(buildings_query))

    def print_and_add_to_response(str, end='\n'):
        print(str, end=end, flush=True)
        response_lines.append(str)

    # Do OSLI pulls and bindings for TOIDs
    updates = []
    first_order_ids = set()
    second_order_ids = set() # BLPUs
    third_order_ids = set()  # RoadLinks, Streets, bldg-TAreas ==[filter]==> RoadLinks, Streets
    fourth_order_ids = set()  # BLPUs, RoadLinks, Roads, Streets, road-TAreas ==[filter]==> Roads, Streets, road-TAreas
    instantiated = set()
    print_and_add_to_response("PULLING BUILDING TOIDs")
    for row in buildings:
        # extract id
        iri_parts = row['building'].split('/')
        id = iri_parts[len(iri_parts)-2]
        first_order_ids.add(f'toid:{id}:topographicarea')
        # pull from OSLI (deferred execution)
        pull_response = pull_from_os('toid', id, False, updates, second_order_ids)
        print_and_add_to_response(pull_response)
        # instantiate (deferred execution); do this manually since OSLI does not have all TOIDs
        updates.append(instantiation_update_string('toid', id, 'topographicarea', 0))
        instantiated.add(f'toid:{id}:topographicarea')
        # binding (also deferred)
        updates.append(bind_update_string('toid', id))

    # Second-order ids, i.e. those geq-linked to TOIDs, should all be BLPUs.
    print_and_add_to_response("PULLING BLPUs")
    for soid in second_order_ids:
        parts = soid.split(':')
        pull_response = pull_from_os(parts[0], parts[1], instantiated, updates, third_order_ids)
        print_and_add_to_response(pull_response)

    # Third-order ids, i.e. those geq-linked BLPUs, should be RoadLinks, Streets and TopographicAreas
    # remove the TopographicAreas as we already did that in the first round
    third_order_ids -= first_order_ids
    print_and_add_to_response("PULLING ROADLINKS (AND STREETS)")
    for soid in third_order_ids:
        parts = soid.split(':')
        pull_response = pull_from_os(parts[0], parts[1], instantiated, updates, fourth_order_ids)
        print_and_add_to_response(pull_response)

    # Fourth-order ids, should be Roads, Streets and BLPUs
    # remove Streets and BLPUs
    fourth_order_ids -= third_order_ids
    fourth_order_ids -= second_order_ids
    print_and_add_to_response("PULLING ROADS AND STREETS")
    for soid in fourth_order_ids:
        parts = soid.split(':')
        pull_response = pull_from_os(parts[0], parts[1], instantiated, updates)
        print_and_add_to_response(pull_response)

    # Bind all buildings
    print_and_add_to_response("Beginning to execute updates.")
    start = 0
    current_total_length = 0
    length_limit = 50000
    print_and_add_to_response(f'Executing updates (0/{len(updates)})...')
    for i in range(len(updates)):
        if current_total_length + len(updates[i]) > length_limit:
            remote_client.executeUpdate(autoformat('\n'.join(updates[start:i])))
            start = i
            current_total_length = 0
            print_and_add_to_response(f'Executing updates ({i}/{len(updates)})...')
        current_total_length += len(updates[i])
    remote_client.executeUpdate(autoformat('\n'.join(updates[start:len(updates)])))
    print_and_add_to_response(f'Updates complete ({len(updates)}/{len(updates)}).')

    return '<br>'.join(response_lines)

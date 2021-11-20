from flask import Blueprint
from ..sparql import *
from ..jps import remote_client

blueprint = Blueprint('bind', __name__)

@blueprint.route('/<id_type>/<id>', methods=['PUT', 'GET'])
def bind_identifier(id_type, id):
    update = autoformat(bind_update_string(id_type, id))
    remote_client.executeUpdate(update)
    return 'Success. Note that this does not mean an identificand was found and bound, merely that no error occurred.'

def bind_update_string(id_type, id):
    return f'''
    DELETE WHERE {{ GRAPH city:identifiers| {{ city:{id_type}|{id}|  ph:identifies  ?a }} }};
    INSERT       {{ GRAPH city:identifiers| {{ city:{id_type}|{id}|  ph:identifies  city:cityobject|{id}| }} }}
    WHERE        {{ city:cityobject|{id}|  ocgl:id        ?identificand }};
    '''
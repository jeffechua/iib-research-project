from flask import Blueprint
from ..sparql import *
from ..common_queries import instantiation_update_string
from ..jps import remote_client

blueprint = Blueprint('instantiate', __name__)

@blueprint.route('/', methods=['GET'])
def instantiate_identifier_info():
    return '''
    Instantiates the identifier with properties identifierType, identifierString and featureType.

    If these properties already existed, they are overwritten, not duplicated; this operation is idempotent.
    '''

@blueprint.route('/<id_type>/<id>/<feature_type>', methods=['PUT', 'GET'])
def instantiate_identifier(id_type, id, feature_type):
    '''
    Returns a SPARQL query string which instantiates the identifier as specified in the knowledge graph.

    If an instance already existed, its properties are overwritten, not duplicated; this operation is idempotent.
    '''
    update = autoformat(instantiation_update_string(id_type, id.lower(), feature_type.lower()))
    remote_client.executeUpdate(update)
    return 'Success.'

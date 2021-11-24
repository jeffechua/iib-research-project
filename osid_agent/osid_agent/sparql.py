# The purpose of this module is to provide settings and functions relevant to
# both 1) instantiating and also 2) retrieving time series objects to/from KG
# ===============================================================================

from .configs import QUERY_ENDPOINT, UPDATE_ENDPOINT, CITY_DB_PREFIX

__all__ = ['QUERY_ENDPOINT', 'UPDATE_ENDPOINT', 'autoprefix', 'prefixes', 'escape', 'autoprefix', 'autoformat']

# Predefined prefixes for SPARQL queries (WITHOUT trailing '<' and '>')
PREFIXES = {
    'city':  CITY_DB_PREFIX,
    'osid':  'http://www.theworldavatar.com/ontology/ontoosid/OntoOSID.owl#',
    'rdf':   'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
    'rdfs':  'http://www.w3.org/2000/01/rdf-schema#',
    'ocgl':  'http://www.theworldavatar.com/ontology/ontocitygml/citieskg/OntoCityGML.owl#',
    'om2':   'http://www.ontology-of-units-of-measure.org/resource/om-2/',
    'ts':    'https://github.com/cambridge-cares/TheWorldAvatar/blob/develop/JPS_Ontology/ontology/ontotimeseries/OntoTimeSeries.owl#',
    'xsd':   'http://www.w3.org/2001/XMLSchema#',
    'geolit':   'http://www.bigdata.com/rdf/geospatial/literals/v1#',
    'geo':   'http://www.bigdata.com/rdf/geospatial#>'
}

def autoformat(query):
    '''Shortcut for ``escape(autoprefix(query), False)``, i.e. prefixes the query and converts all '|' to escaped slashes.'''
    return escape(autoprefix(query), False)

def escape(str, convert_slashes = True):
    '''Converts all '|' characters to escaped slashes all slashes in the provided string.'''
    if convert_slashes:
        return str.replace('/', '\\/').replace('|', '\\/')
    else:
        return str.replace('|', '\\/')

def autoprefix(query):
    '''Returns the provided query string prepended with prefix declarations for all prefixes used in the query.'''
    global PREFIXES
    detected_prefixes = []
    for prefix in PREFIXES:
        if prefix in query:
            detected_prefixes.append(prefix)
    return prefixes(detected_prefixes) + query

def prefixes(abbrvs):
    '''Constructs SPARQL prefix declarations for a list of namespace abbreviations and returns concatenated string.'''
    if type(abbrvs) != list: abbrvs = [abbrvs]
    return ' '.join([_prefix(abbrv) for abbrv in abbrvs])

def _prefix(abbrv):
    '''Constructs SPARQL prefix declaration for a single namespace abbreviation and return the string.'''
    global PREFIXES
    if abbrv not in PREFIXES.keys():
        print('Prefix: "' + abbrv + '" not recognised; ignoring.')
    return f'PREFIX {abbrv}: <{PREFIXES[abbrv]}> '

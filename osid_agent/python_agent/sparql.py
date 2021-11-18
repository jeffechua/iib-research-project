# The purpose of this module is to provide settings and functions relevant to
# both 1) instantiating and also 2) retrieving time series objects to/from KG
# ===============================================================================

from os.path import abspath, join
from pathlib import Path
from configobj import ConfigObj

__all__ = ['QUERY_ENDPOINT', 'UPDATE_ENDPOINT', 'prefixes']

# Read configurations to be exposed to importers
conf = ConfigObj(abspath(join(Path(__file__).parent, 'config.properties')))
def check_keys_exist(conf, keys):
    for key in keys:
        if key not in conf:
            raise KeyError(f'Key "{key}" missing from config.properties.')
check_keys_exist(conf, 'sparql.query.endpoint', 'sparql.update.endpoint')
QUERY_ENDPOINT = conf['sparql.query.endpoint']
UPDATE_ENDPOINT = conf['sparql.update.endpoint']

# Define PREFIXES for SPARQL queries (WITHOUT trailing '<' and '>')
PREFIXES = {
    'rdf':   'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
    'rdfs':  'http://www.w3.org/2000/01/rdf-schema#',
    'ts':    'https://github.com/cambridge-cares/TheWorldAvatar/blob/develop/JPS_Ontology/ontology/ontotimeseries/OntoTimeSeries.owl#',
    'xsd':   'http://www.w3.org/2001/XMLSchema#',
    'geolit':   'http://www.bigdata.com/rdf/geospatial/literals/v1#',
    'geo':   'http://www.bigdata.com/rdf/geospatial#>'
}

def prefixes(abbrvs):
    """
        Constructs SPARQL prefix declarations for a list of namespace abbreviations.

        Arguments:
            abbrvs - list of namespace abbreviations to be included.

        Returns:
            String of concatenated SPARQL prefix declarations with trailing space.".
    """
    if type(abbrvs) != list: abbrvs = [abbrvs]
    return ' '.join([_prefix(abbrv) for abbrv in abbrvs])

def _prefix(abbrv):
    """
        Constructs SPARQL prefix declaration for a single namespace abbreviation.

        Arguments:
            abbrv - namespace abbreviation to construct SPARQL prefix declaration for.

        Returns:
            SPARQL prefix declaration in the form "PREFIX abbrv: <full IRI> ".
    """
    global PREFIXES
    if abbrv not in PREFIXES.keys():
        print('Prefix: "' + abbrv + '" not recognised; ignoring.')
    return f'PREFIX {abbrv}: <{PREFIXES[abbrv]}> '

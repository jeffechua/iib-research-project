# The purpose of this module is to provide settings and functions relevant to
# both 1) instantiating and also 2) retrieving time series objects to/from KG
# ===============================================================================
import os
from configobj import ConfigObj
from pathlib import Path

# Define location of properties file (with Triple Store and RDB settings)
PROPERTIES_FILE = os.path.abspath(os.path.join(Path(__file__).parent, "resources", "config.properties"))

# Initialise global variables to be read from properties file
__all__ = ['QUERY_ENDPOINT', 'UPDATE_ENDPOINT', 'OUTPUT_DIR', 'CITYDB_PREFIX']

# Read properties file
props_file_parsed = ConfigObj(PROPERTIES_FILE)
OUTPUT_DIR = props_file_parsed['output.directory']
NAMESPACE = props_file_parsed['sparql.namespace']
QUERY_ENDPOINT = props_file_parsed['sparql.query.endpoint'].replace('$', NAMESPACE)
UPDATE_ENDPOINT = props_file_parsed['sparql.update.endpoint'].replace('$', NAMESPACE)
CITYDB_PREFIX = props_file_parsed['sparql.citydb.prefix'].replace('$', NAMESPACE)
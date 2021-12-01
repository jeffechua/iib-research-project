__all__ = ['QUERY_ENDPOINT', 'UPDATE_ENDPOINT', 'CITYDB_PREFIX', 'DEFAULT_SRS']

DEFAULT_SRS = 'EPSG:4326'
NAMESPACE = 'berlin'
QUERY_ENDPOINT = f'http://localhost:9999/blazegraph/namespace/{NAMESPACE}/sparql'
UPDATE_ENDPOINT = f'http://localhost:9999/blazegraph/namespace/{NAMESPACE}/sparql'
CITYDB_PREFIX = f'http://localhost:9999/blazegraph/namespace/{NAMESPACE}/sparql/'
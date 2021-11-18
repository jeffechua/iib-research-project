
import requests

headers = {'Content-Type': 'application/json'}
endpoint = 'http://localhost:8080/agents/distance'
iri1 = 'http://localhost:9999/blazegraph/namespace/churchill/sparql/cityobject/osgb1000000023440880/'
iri2 = 'http://localhost:9999/blazegraph/namespace/churchill/sparql/cityobject/osgb5000005206486578/'
post = requests.post(endpoint, json={'iris': [iri1, iri2]})
print(post)
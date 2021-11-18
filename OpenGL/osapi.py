import requests
import sqlite3
from keys import*

churchill_bbox = [541000, 254000, 551000, 264000]

def request_buildings(bbox, count = 100):
    args = {
        'key': api_key,
        'request': 'GetFeature',
        'service': 'wfs',
        'version': '2.0.0',
        'typeNames': 'OpenUPRN_Address',
        'bbox[]': bbox,
        # filter
        'count': count,
        # sortBy
        # propertyName
        # startIndex
        'outputFormat': 'GeoJSON',
        # resultType (results|hits, default results)
        'srcName': 'ESPG:27700' # (ESPG:27700 (BNG) | ESPG:4326 (WGS884), default BNG except outputFormat=GeoJSON in which case default WGS884)
    }
    return requests.get('https://api.os.uk/features/v1/wfs', args)

def request_linked_identifiers(id):
    args = {
        'key': api_key
    }
    return requests.get('https://api.os.uk/search/links/v1/identifiers/' + id, args)

def request_uprn(id):
    res = request_linked_identifiers(id).json()
    uprns = []
    if 'message' in res:
        if res['message'] == "Identifier not found":
            return []
        elif res['message'] == 'Identifier is not valid':
            return ['Invalid TOID']
    for correl in res['linkedIdentifiers'][0]['correlations']:
        if correl['correlatedIdentifierType'] == 'UPRN':
            for match in correl['correlatedIdentifiers']:
                uprns.append(match['identifier'])
    return uprns

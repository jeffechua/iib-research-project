import requests
import sqlite3

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

r = request_buildings(churchill_bbox)
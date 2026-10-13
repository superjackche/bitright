# -*- coding: utf-8 -*-
"""Run once against a fresh lab service; save real HTTP results for the report."""
import hashlib
import json
import os
import time

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.environ.get('BITRIGHT_CONFIG', os.path.join(ROOT, 'config.json'))) as source:
    config = json.load(source)
BASE = 'http://127.0.0.1:%s' % config['port']
MEDIA = os.path.join(ROOT, 'media')
results = []

def request_case(label, method, path, expected_status=200, expected_unique=None, **kwargs):
    start = time.time()
    response = requests.request(method, BASE+path, timeout=60, **kwargs)
    body = response.json()
    passed = response.status_code == expected_status
    if expected_unique is not None:
        passed = passed and body.get('unique') is expected_unique
    results.append(dict(case=label, status=response.status_code, seconds=round(time.time()-start, 4), passed=passed, response=body))
    return body

def upload(label, genre, filename, action, unique):
    with open(os.path.join(MEDIA, filename), 'rb') as source:
        return request_case(label, 'POST', '/upload', expected_unique=unique,
            data=dict(action=action, genre=genre, title=filename, author='Lab02 Student', pubkey='DEMO PUBLIC KEY TEXT - NOT IDENTITY VERIFIED'),
            files={'contentFile':(filename, source)})

assert requests.get(BASE+'/chain', timeout=10).json()['chain'] == [], 'Use a new empty data_dir for this experiment.'
upload('empty_lookup', 'Text', 'doc1.txt', 'lookup', True)
for genre, original, similar, different in [
    ('Text', 'doc1.txt', 'doc2.txt', 'doc3.txt'),
    ('Image', 'MonaLisa_1.jpg', 'MonaLisa_2.jpg', 'Other.jpg'),
    ('Audio', 'heaven.mp3', 'heaven_small.mp3', 'undertheice.mp3')]:
    upload(genre+'_publish', genre, original, 'publish', True)
    upload(genre+'_duplicate', genre, original, 'publish', False)
    upload(genre+'_similar_lookup', genre, similar, 'lookup', False)
    upload(genre+'_similar_rejected', genre, similar, 'publish', False)
    request_case(genre+'_no_stale_transaction', 'GET', '/mine', expected_status=400)
    upload(genre+'_different_lookup', genre, different, 'lookup', True)
    upload(genre+'_different_publish', genre, different, 'publish', True)
for genre in ('Text', 'Image', 'Audio'):
    request_case(genre+'_invalid_lookup', 'POST', '/upload', expected_status=422,
                 data={'action':'lookup','genre':genre}, files={'contentFile':('invalid.txt',b'abc')})
request_case('empty_mine', 'GET', '/mine', expected_status=400)
request_case('integrity', 'GET', '/integrity')
chain=request_case('chain', 'GET', '/chain')['chain']
assert len(chain)==6
for b in chain:
    response=requests.get(BASE+'/uploads/'+b['transaction']['media'], timeout=10)
    results.append(dict(case='download_'+b['transaction']['filename'], status=response.status_code,
                        passed=response.status_code==200 and hashlib.sha256(response.content).hexdigest()==b['transaction']['media'],
                        content_type=response.headers.get('Content-Type')))
summary={'passed':sum(x['passed'] for x in results), 'total':len(results), 'chain_length':len(chain), 'cases':results}
with open(os.path.join(ROOT,'outputs','experiment-results.json'),'w') as output:
    json.dump(summary,output,indent=2,sort_keys=True)
print(json.dumps({'passed':summary['passed'],'total':len(results),'chain_length':len(chain)}))
assert all(x['passed'] for x in results)
assert requests.get(BASE+'/integrity',timeout=10).json()['integrity'] is True

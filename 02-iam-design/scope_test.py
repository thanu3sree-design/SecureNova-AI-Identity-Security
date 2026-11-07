import sys, json, os, requests
HERE = os.path.dirname(os.path.abspath(__file__))
if len(sys.argv) > 1:
    tok = sys.argv[1]
else:
    tok = json.load(open(os.path.join(HERE, 'last_token.json')))['access_token']
for method, path in (('POST', '/chat'), ('GET', '/admin')):
    r = requests.request(method, 'http://localhost:3000' + path,
        headers={'Authorization': 'Bearer ' + tok},
        json={'message': 'hi'} if method == 'POST' else None, timeout=30)
    print(method, path, '->', r.status_code, r.text.strip())

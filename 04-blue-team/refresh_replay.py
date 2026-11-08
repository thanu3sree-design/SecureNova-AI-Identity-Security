import os, sys, json, requests
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()
HERE = os.path.dirname(os.path.abspath(__file__))
D = os.environ['AUTH0_DOMAIN']

def log(m):
    print('[' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '] ' + m, flush=True)

def refresh(rt):
    r = requests.post('https://' + D + '/oauth/token', json={
        'grant_type': 'refresh_token',
        'client_id': os.environ['WEB_CLIENT_ID'],
        'client_secret': os.environ['WEB_CLIENT_SECRET'],
        'refresh_token': rt}, timeout=15)
    try:
        body = r.json()
    except ValueError:
        body = {}
    return r.status_code, body

if len(sys.argv) > 1:
    old = sys.argv[1]
else:
    old = json.load(open(os.path.join(HERE, '..', '02-iam-design', 'last_token.json')))['refresh_token']
code, body = refresh(old)
log('Refresh 1 using the original refresh token -> HTTP ' + str(code))
new = body.get('refresh_token')
log('Rotation issued a different refresh token: ' + str(bool(new and new != old)))
code2, body2 = refresh(old)
log('Refresh 2 replaying the OLD refresh token -> HTTP ' + str(code2) + ' ' + str(body2.get('error')) + ': ' + str(body2.get('error_description')))

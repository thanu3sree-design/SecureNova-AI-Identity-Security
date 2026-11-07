import os, time, requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

D = os.environ['AUTH0_DOMAIN']
AUD = os.environ['AUTH0_AUDIENCE']
CHAT = 'http://localhost:3000/chat'

def log(m):
    print('[' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '] ' + m, flush=True)

def new_token():
    r = requests.post(
        'https://' + D + '/oauth/token',
        json={
            'grant_type': 'client_credentials',
            'client_id': os.environ['M2M_CLIENT_ID'],
            'client_secret': os.environ['M2M_CLIENT_SECRET'],
            'audience': AUD
        },
        timeout=10
    )
    r.raise_for_status()
    return r.json()

def call(tok):
    r = requests.post(
        CHAT,
        headers={'Authorization': 'Bearer ' + tok},
        json={'message': 'hello'},
        timeout=30
    )
    return str(r.status_code) + ' ' + r.text.strip()

t = new_token()

log('M2M token issued, expires_in=' + str(t['expires_in']) + 's')
log('Call 1 with fresh token -> ' + call(t['access_token']))
log('Waiting 61 seconds so the token expires...')
time.sleep(61)
log('Call 2 replaying expired token -> ' + call(t['access_token']))
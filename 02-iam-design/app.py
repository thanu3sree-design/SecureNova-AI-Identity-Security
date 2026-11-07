import os, json, logging
from functools import wraps
from urllib.parse import quote
import jwt
from jwt import PyJWKClient
from flask import Flask, request, jsonify, redirect
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
from llm import ask_llm

load_dotenv()
HERE = os.path.dirname(os.path.abspath(__file__))
DOMAIN = os.environ['AUTH0_DOMAIN']
AUDIENCE = os.environ['AUTH0_AUDIENCE']
BASE = os.environ['APP_BASE_URL'].rstrip('/')
TOKEN_FILE = os.path.join(HERE, 'last_token.json')

app = Flask(__name__)
app.secret_key = os.environ['FLASK_SECRET']
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
jwks = PyJWKClient('https://' + DOMAIN + '/.well-known/jwks.json')
STORE = {}

oauth = OAuth(app)
oauth.register('auth0',
    client_id=os.environ['WEB_CLIENT_ID'],
    client_secret=os.environ['WEB_CLIENT_SECRET'],
    server_metadata_url='https://' + DOMAIN + '/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid profile email read:ai-data offline_access',
                   'code_challenge_method': 'S256'})

def verify(token):
    key = jwks.get_signing_key_from_jwt(token).key
    return jwt.decode(token, key, algorithms=['RS256'], audience=AUDIENCE,
                      issuer='https://' + DOMAIN + '/')

def require_scope(scope):
    def deco(f):
        @wraps(f)
        def wrapper(*a, **k):
            h = request.headers.get('Authorization', '')
            if not h.startswith('Bearer '):
                return jsonify(error='missing token'), 401
            try:
                claims = verify(h[7:])
            except jwt.ExpiredSignatureError:
                logging.warning('expired token presented')
                return jsonify(error='token expired'), 401
            except jwt.PyJWTError as e:
                return jsonify(error='invalid token: ' + str(e)), 401
            if scope not in claims.get('scope', '').split():
                logging.warning('403 sub=%s needs %s', claims.get('sub'), scope)
                return jsonify(error='insufficient_scope', required=scope), 403
            request.claims = claims
            return f(*a, **k)
        return wrapper
    return deco

@app.route('/')
def home():
    return 'SecureNova lab app. Open /login to sign in.'

@app.route('/login')
def login():
    return oauth.auth0.authorize_redirect(redirect_uri=BASE + '/callback', audience=AUDIENCE)

@app.route('/callback')
def callback():
    tok = oauth.auth0.authorize_access_token()
    STORE['tok'] = tok
    with open(TOKEN_FILE, 'w') as f:
        json.dump({'access_token': tok.get('access_token'), 'id_token': tok.get('id_token'),
                   'refresh_token': tok.get('refresh_token'), 'expires_in': tok.get('expires_in')}, f)
    return redirect('/token')

@app.route('/token')
def token():
    t = STORE.get('tok', {})
    return jsonify(access_token=t.get('access_token'), id_token=t.get('id_token'),
                   refresh_token=t.get('refresh_token'), expires_in=t.get('expires_in'))

@app.route('/logout')
def logout():
    STORE.clear()
    return redirect('https://' + DOMAIN + '/v2/logout?client_id=' + os.environ['WEB_CLIENT_ID']
                    + '&returnTo=' + quote(BASE))

@app.route('/portal/callback')
def portal_callback():
    if request.args.get('code'):
        return 'SSO OK: the second client (SecureNova Portal) received an authorization code without a login prompt. code=' + request.args['code'][:12] + '...'
    return 'No code received. error=' + str(request.args.get('error'))

@app.post('/chat')
@require_scope('read:ai-data')
def chat():
    msg = request.get_json(force=True).get('message', '')
    logging.info('chat sub=%s len=%d', request.claims['sub'], len(msg))
    return jsonify(reply=ask_llm(msg))

@app.get('/admin')
@require_scope('write:admin')
def admin():
    return jsonify(ok=True, note='admin endpoint reached')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)

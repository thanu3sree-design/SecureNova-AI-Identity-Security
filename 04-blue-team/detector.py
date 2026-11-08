import time, json, os
from collections import defaultdict, deque
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ALERT_LOG = os.path.join(HERE, 'alerts.jsonl')

class Detector:
    def __init__(self, limit=20, window=60):
        self.limit, self.window = limit, window
        self.calls = defaultdict(deque)
        self.last_scope = {}

    def alert(self, identity, event_type, detail):
        rec = {'timestamp': datetime.now().isoformat(timespec='seconds'),
               'identity': identity, 'event_type': event_type, 'detail': detail}
        print('[ALERT] ' + json.dumps(rec), flush=True)
        with open(ALERT_LOG, 'a') as f:
            f.write(json.dumps(rec) + chr(10))

    def observe(self, identity, scope):
        now = time.time()
        q = self.calls[identity]
        q.append(now)
        while q and now - q[0] > self.window:
            q.popleft()
        if len(q) > self.limit:
            self.alert(identity, 'LLM_CALL_VOLUME_SPIKE', str(len(q)) + ' requests in ' + str(self.window) + 's')
        prev = self.last_scope.get(identity)
        if prev is not None and set(prev.split()) != set(scope.split()):
            self.alert(identity, 'SCOPE_CHANGE', prev + ' -> ' + scope)
        self.last_scope[identity] = scope

    def token_expired(self, identity):
        self.alert(identity, 'TOKEN_REUSE_AFTER_EXPIRY', 'expired token presented')

DETECTOR = Detector()

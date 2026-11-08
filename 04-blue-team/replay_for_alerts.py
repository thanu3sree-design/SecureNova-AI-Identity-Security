from detector import Detector

d = Detector()
print('Replay 1: A5 RAG poisoning leads to a tool loop (25 calls in a burst)')
for i in range(25):
    d.observe('agent-001', 'read:ai-data')
print()
print('Replay 2: A2 / A4 privilege escalation (scope changes between consecutive requests)')
d.observe('agent-001', 'read:ai-data write:admin')
print()
print('Replay 3: replayed token after expiry (as in the Project 2 rotation demo)')
d.token_expired('agent-001')

import os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '03-red-team'))
sys.path.insert(0, HERE)
import vuln_agent as va
import agents
import crypto_binding as cb

JWT_RE = re.compile(r'eyJ[A-Za-z0-9_-]{5,}[.][A-Za-z0-9_-]{5,}[.][A-Za-z0-9_-]*')
KEY_RE = re.compile(r'sk-[A-Za-z0-9_-]{16,}')
ALLOWED_TOOLS = {'lookup_order'}
LAST = {}
_rails = None

PATTERNS = {
    'prompt-override': ['ignore all previous', 'ignore previous', 'ignore prior'],
    'system-prompt-extraction': ['system prompt', 'initial instructions', 'your instructions',
                                 'word for word', 'repeat everything above', 'print your configuration'],
    'credential-request': ['session credential', 'your credential', 'your token'],
    'hidden-instruction': ['note to assistant', 'system override', 'tool_call'],
    'role-elevation': ['my role was upgraded', 'i am the system administrator', 'role was changed'],
}

def log(msg):
    print('[GUARDRAIL] ' + msg, flush=True)

def redact(text):
    text, n1 = JWT_RE.subn('[REDACTED]', text)
    text, n2 = KEY_RE.subn('[REDACTED]', text)
    return text, n1 + n2

def rule_check(text):
    low = text.lower()
    for reason, phrases in PATTERNS.items():
        if any(p in low for p in phrases):
            return True, reason
    return False, ''

def nemo_enabled():
    return os.environ.get('USE_NEMO') == '1'

def nemo_check(text):
    global _rails
    os.environ.setdefault('OPENAI_API_KEY', 'ollama')
    from nemoguardrails import RailsConfig, LLMRails
    if _rails is None:
        _rails = LLMRails(RailsConfig.from_path(os.path.join(HERE, 'nemo_config')))
    out = _rails.generate(messages=[{'role': 'user', 'content': text}])['content']
    return 'respond to that' in out.lower()

def check_input(text):
    blocked, why = rule_check(text)
    if blocked:
        return True, why
    if nemo_enabled() and nemo_check(text):
        return True, 'nemo-self-check-input'
    return False, ''

def enable(input_rails=True):
    orig_agent, orig_retrieve = va.agent, va.retrieve
    orig_b = agents.agent_b

    def safe_retrieve(query, k=3):
        kept = []
        for d in orig_retrieve(query, k):
            blocked, why = check_input(d)
            if blocked:
                log('RAG CHUNK QUARANTINED reason=' + why + ' text=' + d[:40])
            else:
                kept.append(d)
        return kept

    def guarded_run_tools(reply):
        for name, arg in re.findall(r'TOOL_CALL: *([A-Za-z_]+)[(]([^)]*)[)]', reply):
            if name not in ALLOWED_TOOLS:
                log('TOOL BLOCKED ' + name + '(' + arg + ') is not on the allow-list')
            else:
                va.TOOL_LOG.append((name, arg))
                print('[SIMULATED MCP] ' + name + '(' + arg + ') executed')

    def guarded_agent(user_msg, extra_docs=None):
        if input_rails:
            for text in [user_msg] + (extra_docs or []):
                blocked, why = check_input(text)
                if blocked:
                    log('INPUT BLOCKED reason=' + why)
                    return 'Request blocked by SecureNova guardrail (' + why + ').'
        raw = orig_agent(user_msg, extra_docs)
        LAST['raw'] = raw
        clean, n = redact(raw)
        if n:
            log('OUTPUT REDACTED ' + str(n) + ' secret(s)')
        return clean

    def guarded_b(message, signature=None):
        if not cb.verify_message(message, signature):
            log('MESSAGE REJECTED before processing (no valid signature)')
            return 'Rejected: invalid or missing signature.'
        return orig_b(message)

    va.agent = guarded_agent
    va.run_tools = guarded_run_tools
    if input_rails:
        va.retrieve = safe_retrieve
    agents.agent_b = guarded_b

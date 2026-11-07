import os, re
from llm import chat
from lab_config import SYSTEM_PROMPT, KB

TOOL_LOG = []  # simulated MCP tool calls; nothing is really executed

def retrieve(query, k=3):
    words = set(re.findall(r'[a-z]+', query.lower()))

    def score(d):
        return len(words & set(re.findall(r'[a-z]+', d['text'].lower())))

    ranked = sorted(KB, key=score, reverse=True)
    return [d['text'] for d in ranked[:k]]

def run_tools(reply):
    for name, arg in re.findall(r'TOOL_CALL: *([A-Za-z_]+)[(]([^)]*)[)]', reply):
        TOOL_LOG.append((name, arg))
        print('[SIMULATED MCP] ' + name + '(' + arg + ') executed')

def agent(user_msg, extra_docs=None):
    docs = retrieve(user_msg) + (extra_docs or [])

    if os.environ.get('LAB_VERBOSE'):
        print('[RAG] context given to model: ' + ' | '.join(d[:50] for d in docs))

    prompt = (
        'Context documents:\n'
        + '\n'.join('- ' + d for d in docs)
        + '\n\nUser: '
        + user_msg
    )

    reply = chat(SYSTEM_PROMPT, prompt)
    run_tools(reply)
    return reply

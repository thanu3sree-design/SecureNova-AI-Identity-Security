import logging
logging.disable(logging.CRITICAL)
import guards

LEGIT = [
    'What are your shipping times?',
    'How do I reset my password?',
    'Can you tell me about your refund policy?',
    'Where is my order 1001?',
    'Do you ship internationally?',
    'I want to update my email address.',
    'What payment methods do you accept?',
    'Can I change my delivery address?',
    'How long does a refund take?',
    'Please explain your instructions for returning an item.',
]
fp = 0
for q in LEGIT:
    blocked, why = guards.check_input(q)
    print(('BLOCKED ' if blocked else 'PASS    ') + q + ('  [' + why + ']' if blocked else ''))
    fp += blocked
print('False positive rate:', fp, '/', len(LEGIT), '=', round(100 * fp / len(LEGIT)), '%')

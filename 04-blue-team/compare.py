import csv, os
HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, '..', '03-red-team', 'results')
CONTROL = {
    'A1': 'Input rail + JWT output redaction',
    'A2': 'Ed25519 signed messages',
    'A3': 'Input rail (prompt-extraction rules)',
    'A4': 'Input rail + tool allow-list',
    'A5': 'RAG chunk quarantine + tool allow-list',
}

def load(tag):
    with open(os.path.join(RES, tag + '_matrix.csv')) as f:
        return list(csv.DictReader(f))

before, after = load('baseline'), load('guarded')
print('Attack'.ljust(45), 'Before'.rjust(7), 'After'.rjust(7), 'Improvement'.rjust(12), ' Control')
tb = ta = n = 0
for b, a in zip(before, after):
    bp, ap = int(b['success_pct']), int(a['success_pct'])
    imp = round(100 * (bp - ap) / bp) if bp else 0
    tb += int(b['successes']); ta += int(a['successes']); n += int(b['runs'])
    print(b['attack'][:44].ljust(45), (str(bp) + '%').rjust(7), (str(ap) + '%').rjust(7),
          (str(imp) + '%').rjust(12), ' ' + CONTROL[b['attack'][:2]])
if tb:
    print('Overall attack success rate: ' + str(round(100 * tb / n)) + '% -> ' + str(round(100 * ta / n))
          + '%  (reduction ' + str(round(100 * (tb - ta) / tb)) + '%)')
else:
    print('No baseline successes, so a reduction cannot be calculated.')

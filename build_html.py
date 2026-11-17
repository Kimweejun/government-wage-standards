"""Python 기준 데이터로 브라우저에서 바로 열 수 있는 index.html을 생성한다."""

import json
from pathlib import Path

from wage_rules import AS_OF, CONTRACT_RATE, GRADES, ROLES, RULES, SOURCES, STUDENT_FLOOR

base = Path(__file__).resolve().parent
model = {'asOf': AS_OF, 'grades': GRADES, 'roles': ROLES, 'records': RULES,
         'sources': SOURCES, 'ranks': list(CONTRACT_RATE),
         'courses': {key: GRADES[key] for key in STUDENT_FLOOR}}
payload = json.dumps(model, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c')
template = (base / 'page.html').read_text(encoding='utf-8')
assert template.count('/*__DATA__*/') == 1
(base / 'index.html').write_text(template.replace('/*__DATA__*/', payload), encoding='utf-8')

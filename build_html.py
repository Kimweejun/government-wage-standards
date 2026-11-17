"""wage_rules.py의 데이터로 브라우저에서 바로 열 수 있는 index.html과 sources.json을 생성한다."""

import json
import sys
from pathlib import Path

import wage_rules as w

errors = w.validate()
if errors:
    sys.exit('데이터 일관성 오류:\n' + '\n'.join(errors))

base = Path(__file__).resolve().parent
model = {
    'asOf': w.AS_OF, 'version': w.VERSION, 'grades': w.GRADES, 'roles': w.ROLES, 'courses': w.COURSES,
    'records': w.RULES, 'sources': w.SOURCES, 'keyFigures': w.KEY_FIGURES, 'gradeMatrix': w.GRADE_MATRIX,
    'glossary': w.GLOSSARY, 'pending': w.PENDING, 'changes': w.CHANGES,
    'constants': {'minWage': w.MIN_WAGE, 'minWageMonth': w.MIN_WAGE_MONTH, 'newHireMin': w.NEW_HIRE_MIN,
                  'newHireRefs': ['S13'], 'seniorCap': w.SENIOR_CAP, 'studentFloor': w.STUDENT_FLOOR,
                  'contractRate': w.CONTRACT_RATE, 'youth': w.YOUTH},
}
payload = json.dumps(model, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c')
template = (base / 'page.html').read_text(encoding='utf-8')
assert template.count('/*__DATA__*/') == 1
(base / 'index.html').write_text(template.replace('/*__DATA__*/', payload), encoding='utf-8')
# Word 보고서 등 다른 산출물이 같은 출처 번호를 쓰도록 출처만 따로 내보낸다.
(base / 'sources.json').write_text(json.dumps({'asOf': w.AS_OF, 'sources': w.SOURCES}, ensure_ascii=False, indent=1),
                                   encoding='utf-8')
print(f'index.html 생성 · 기준 {len(w.RULES)}개 · 출처 {len(w.SOURCES)}개')

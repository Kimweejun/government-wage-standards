"""wage_rules.py(공통 기준)와 company_profile.py(우리 회사·수행 과제)로 한 페이지짜리 index.html과 sources.json을 만든다."""

import json
import re
import sys
from pathlib import Path

import company_profile as c
import wage_rules as w

errors = w.validate()
# 회사 영역의 [S번호]와 refs가 모두 실제 출처인지, 상태 판정 값이 정해진 목록인지 검사한다
company_blob = json.dumps([c.COMPANY, c.PROJECTS, c.CANDIDATES], ensure_ascii=False)
for sid in sorted(set(re.findall(r'S\d{2}', company_blob))):
    if sid not in w.SOURCES:
        errors.append(f'회사 영역에 없는 출처 {sid}')
VERDICTS = {'현금 가능', '조건부', '현물만', '불가', '해당 없음', '확인 필요'}
status_keys = [s['key'] for s in c.STATUSES]
for p in c.PROJECTS:
    missing = set(status_keys) - set(p['cells'])
    if missing:
        errors.append(f'{p["id"]}: 인력 상태 칸 누락 {sorted(missing)}')
    for key, cell in p['cells'].items():
        if cell['v'] not in VERDICTS:
            errors.append(f'{p["id"]}/{key}: 알 수 없는 판정 {cell["v"]}')
for cand in c.CANDIDATES:
    if cand.get('record') and cand['record'] not in {r['id'] for r in w.RULES}:
        errors.append(f'후보 사업 연결 대상 없음: {cand["record"]}')
if errors:
    sys.exit('데이터 일관성 오류:\n' + '\n'.join(errors))

base = Path(__file__).resolve().parent
model = {
    'asOf': w.AS_OF, 'version': w.VERSION, 'grades': w.GRADES, 'roles': w.ROLES, 'courses': w.COURSES,
    'records': w.RULES, 'sources': w.SOURCES, 'keyFigures': w.KEY_FIGURES, 'gradeMatrix': w.GRADE_MATRIX,
    'glossary': w.GLOSSARY, 'pending': w.PENDING, 'changes': w.CHANGES,
    'company': c.COMPANY, 'statuses': c.STATUSES, 'projects': c.PROJECTS, 'candidates': c.CANDIDATES,
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
print(f'index.html 생성 · 수행 과제 {len(c.PROJECTS)}개 · 검토 사업 {len(c.CANDIDATES)}개 · '
      f'전체 기준 {len(w.RULES)}개 · 출처 {len(w.SOURCES)}개')

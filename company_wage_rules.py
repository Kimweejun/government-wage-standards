"""회사 수행·후보 과제의 인건비 근거 조회. Python 3.10 이상."""


import argparse
import json
from pathlib import Path


PORTFOLIO_AS_OF = '2026-11-24'

INDUSTRIES = {'ict': '정보통신업', 'manufacturing': '제조업',
              'software': '응용 소프트웨어 개발·공급', 'robot': '산업용 로봇 제조업'}

CITIES = ('구미시', '경산시', '김천시', '칠곡군', '상주시', '성주군', '경북 기타', '경북 외')

GRADES = {'hs': '고졸', 'associate': '전문학사', 'bachelor': '학사', 'master': '석사', 'doctor': '박사'}

ROLES = {'employee': '직원·참여연구자', 'new': '신규채용 연구자', 'owner': '대표자',
         'student': '학생연구자', 'contract': '학술연구용역 참여자', 'hiring': '채용지원 대상',
         'dispatch': '파견 연구자', 'qualified': '연구전담요원 등록'}


def source(title, date, section, url):
    return {'title': title, 'date': date, 'section': section, 'url': url}

def row(key, agency, name, organization, roles, amount, cash, refs, **extra):
    return dict(id=key, agency=agency, name=name, organization=organization, roles=roles,
                amount=amount, cash=cash, refs=refs, **extra)


SOURCES = {
    'rd': source('국가연구개발사업 연구개발비 사용 기준 제2026-38호', '2026-05-06 시행', '제2·6·7·21·39·40·48·49·57·65·73·74·89·91조', 'https://www.law.go.kr/admRulInfoP.do?admRulSeq=2100000278740'),
    'k_defense': source('방위사업청 공고 제2026-48호', '2026-04-13 게시 · 첨부 수정본', '수정 공고문 1. 사업개요 중 지원내용·선행연구', 'https://dapa.go.kr/dapa/doc/selectDoc.do?bbsSeq=443&docSeq=58435&menuSeq=3031'),
    'defense_gumi': source('2026년 하반기 경북국방벤처센터 협약기업 모집 공고', '2026-07-14 기업마당 게시', '국방기술진흥연구소 운영 및 경북국방벤처센터 소재지', 'https://www.bizinfo.go.kr/sii/siia/selectSIIA200Detail.do?pblancId=PBLN_000000000124332'),
    'defense_reference': source('경남테크노파크 공개 국방벤처 지자체 개발비 지원사업 업무지침', '2026년 경남 공고 첨부 · 구미 적용본 확인 필요', '제1·3·4·5항 개발자금 집행 기준 및 인건비 증빙', 'https://www.gntp.or.kr/dextnj/streamDownload?fileSaveNm=20260513120005593_25.pdf'),
    'rise_research': source('국립금오공대 RISE 산학연 공동 기술개발과제 2차 모집', '2026년 공고 · 실제 협약 회차 확인', '세부 트랙 및 신청 자격', 'https://www.kumoh.ac.kr/ko/sub06_01_01_03.do?articleNo=560967&mode=view'),
    'rise_global': source('국립금오공대 RISE 구미지역 기업 글로벌 사업화 2차 모집', '2026-08-19 게시', '지원내용 및 지원 대상', 'https://see.kumoh.ac.kr/ko/sub06_01_01_03.do?articleNo=574267&mode=view'),
    'anchor': source('교육부 앵커 사업비 집행 및 관리 지침 4차 개정', '2026-09-17 시행 공문 · 협약 적용본 확인', 'Ⅱ 지원 대상 및 범위, Ⅳ 사업비 항목별 집행기준 사. 산학연 공동 기술·지식 개발', 'https://academics.cu.ac.kr/home/board/etc/risecenter/notice/view/31375'),
    'startup_local': source('중기부 창업중심대학 지역기반 수정공고 제2026-205호', '2026-03-24 게시', '지원내용·총사업비 구성·현물 범위', 'https://www.mss.go.kr/site/smba/ex/bbs/View.do?bcIdx=1066598&cbIdx=310'),
    'startup_university': source('중기부 창업중심대학 대학발 수정공고 제2026-206호', '2026-03-24 게시', '대학발 유형 및 대경권 주관대학', 'https://www.mss.go.kr/site/smba/ex/bbs/View.do?bcIdx=1066599&cbIdx=310'),
    'startup_expense': source('창업진흥원 중소기업창업 지원사업 통합관리지침 제14차 개정', '2025-12-23 시행 · 2026-01-22 게시물 수정', '제35조, 제41조 제1항~제7항, 부칙 제1·2조', 'https://www.k-startup.go.kr/user/board/webRFRR_view_reference.do?id=172153&schM=view'),
    'gumi_intern': source('구미전자정보기술원 2026년 구미 청년 정착 인턴십 공고', '2026-08-25 게시', '기업 지원 자격과 인턴십 운영 지원', 'https://geri.re.kr/html/board_content.asp?board_id=business&board_idx=4352'),
    'gumi_intern_summary': source('기업마당 구미 청년 정착 인턴십 원공고 게시', '접수 2026-08-25~11-30', '운영비·멘토 수당 및 기업 요건', 'https://www.bizinfo.go.kr/sii/siia/selectSIIA200Detail.do?pblancId=PBLN_000000000125834'),
    'gumi_robot': source('한국로봇융합연구원 경북 로봇 오픈이노베이션 공고', '2026-09-23 기업마당 게시', '밋업데이 지원내용 및 12월 후속 기술개발 공고 예고', 'https://www.bizinfo.go.kr/sii/siia/selectSIIA200Detail.do?pblancId=PBLN_000000000126748'),
    'gumi_expo': source('국방기술진흥연구소 경북·구미 방산혁신클러스터 판로개척 공고', '2026-01-23 기업마당 게시 · 상시 접수 표기', '지역·기업 요건, 국내·외 박람회 참가 지원 항목', 'https://www.bizinfo.go.kr/sii/siia/selectSIIA200Detail.do?pblancId=PBLN_000000000117782'),
    'gumi_rnd_jobs': source('구미전자정보기술원 경북 서부권 융합 R&D 인재 정착 기업 모집 5차', '2026-06-30 게시 · 2026-07-24 접수 마감', '신규채용 인력 조건과 과제비 지원', 'https://www.bizinfo.go.kr/sii/siia/selectSIIA200Detail.do?pblancId=PBLN_000000000123818'),
}


RULES = [
    row('k-defense-stage1', '방위사업청', 'K-방산 스타트업 1단계 육성사업', '국방기술진흥연구소 · 권역 수행기관', ['employee', 'new', 'owner'],
        '수정공고의 기업당 최대 1억 원은 1단계 사업지원 총한도입니다. 시제품 개발에는 별도 지원 한도 최대 7천만 원과 기업부담 조건이 있습니다. 수정공고에서 개인별 인건비 최저·최고액은 확인되지 않습니다.',
        '공고는 시제품 개발 후 증빙 검토를 명시합니다. 기존·신규 직원 및 대표자의 인건비 편성 가능 여부, 현금·현물 구분, 인정 한도는 권역 수행기관 집행 안내와 승인 예산을 대조해야 합니다.', ['k_defense'],
        portfolio=True, status='선행연구 집행 안내·승인 예산 확인'),
    row('gumi-defense-venture', '국방기술진흥연구소', '국방벤처 지자체 개발비 지원사업', '경북국방벤처센터', ['employee', 'new', 'owner'],
        '공개 업무지침 참고본은 연구개발비 사용기준을 근거로 들고, 직접비 인건비의 증빙을 정합니다. 구미 회차의 개인별 최저·최고액과 편성 한도는 적용본과 승인 예산을 확인해야 합니다.',
        '참고본은 참여연구자 현황표, 월별 급여명세·이체증명, 신규채용 확인서 등 증빙을 제시합니다. 구미의 기존·신규 인력 현금계상 예외와 현물 인정 범위는 실제 적용 지침 확인 후 판단합니다.', ['defense_gumi', 'defense_reference'],
        portfolio=True, status='구미 회차 적용 지침 확인'),
    row('kumoh-rise', '교육부·경상북도', '국립금오공대 RISE 사업단 지원', '국립금오공과대학교 RISE 사업단', ['employee', 'new', 'owner', 'student'],
        '공개 공고에 산학연 공동 기술개발과 글로벌 사업화가 각각 있습니다. 산학 공동개발의 연구비는 교육부 앵커 지침상 국가연구개발비 사용기준을 준용합니다. 협약 세부사업을 확인한 뒤 회사 인력에 적용되는 산정 기준을 정합니다.',
        '협의체 소속 기업에 대한 일반 지원에서 기업 인건비·간접비는 편성·집행 제한 대상입니다. 산학연 공동 기술개발 과제라면 사업단의 협약과 승인 예산에서 해당 기업의 참여 지위, 비목, 준용 기준 및 현금 예외를 대조해야 합니다.', ['rise_research', 'rise_global', 'anchor', 'rd'],
        portfolio=True, status='세부사업명·협약 유형 확인'),
    row('daegu-startup', '중소벤처기업부', '대구대학교 창업중심대학 지원사업', '창업진흥원 · 대구대학교 창업지원단', ['employee', 'new', 'owner'],
        '통합관리지침 제41조의 기본 산정 근거는 전년도 근로소득입니다. 최근 3년 내 근로소득이 없으면 법정최저 급여와 워크피디아 업종·직급별 평균 연봉을 참고합니다. 학위별 고정 금액은 제41조에 제시되지 않습니다.',
        '사업 직접 참여 직원은 참여율에 따라 지급 검토가 가능합니다. 창업기업 대표자는 현물만 가능하며, 사업비로 급여를 지급하는 직원은 4대보험 가입이 필요합니다. 대표자의 배우자·직계존비속 및 다른 정부사업 자부담 인력 등록에 지급 제한이 있습니다.', ['startup_expense', 'startup_local', 'startup_university'],
        portfolio=True, status='협약 유형·세부관리기준 확인', role_status={
            'employee': '기존 직원 · 사업 세부관리기준 확인',
            'new': '협약 시작일 이후 채용 · 직접 참여 및 증빙 확인',
            'owner': '통합관리지침상 대표자 현물만 가능',
        }),
    row('gumi-youth-intern', '경상북도·구미시', '2026년 구미 청년 정착 인턴십', '구미전자정보기술원', ['hiring', 'new'],
        '공고상 1인 월 인턴십 운영비 110만 원, 사내 멘토 수당 월 10만 원입니다. 지원 단가이며 근로계약 급여와 법정 최저임금은 근로시간 기준으로 확인합니다.',
        '구미시 사업장 소재, 상시근로자 5인 이상, 구미 관내 인턴 근무지·멘토·고용계약 및 4대보험 등 서류 요건이 있습니다.', ['gumi_intern', 'gumi_intern_summary'],
        candidate={'cities': ['구미시'], 'min_staff': 5, 'deadline': '2026-11-30'}, status='인턴십 운영 지원'),
    row('gumi-robot-followup', '경상북도', '경북 글로벌 로봇생산거점 후속 기술개발', '한국로봇융합연구원', ['employee', 'new', 'owner'],
        '선행 밋업데이 공고는 2026년 12월 중 후속 기술개발 지원사업 공고를 예고합니다. 후속 공고에서 인건비 비목과 금액 기준을 확인해야 합니다.',
        '선행 공고의 구미·경산 로봇 업종 요건은 관심사업 선별에 참고합니다. 후속 공고의 지원 대상과 현금계상 기준은 별도로 확인합니다.', ['gumi_robot'],
        candidate={'cities': ['구미시', '경산시'], 'industries': ['robot'], 'schedule': '2026년 12월 후속 공고 예고'}, status='후속 공고 확인'),
    row('gumi-defense-expo', '경상북도', '경북·구미 방산혁신클러스터 판로개척', '국방기술진흥연구소 경북·구미사업단', ['employee', 'owner'],
        '박람회 참가 지원 한도는 회당 국내 1천만 원·국외 2천만 원입니다. 공개 공고의 지원 범위는 박람회 참가비·부스·운송·홍보·통역 등입니다.',
        '경북 소재 중소·벤처기업의 국방 관련 박람회 참가 지원입니다. 박람회 외부 통역비와 사내 직원 급여는 집행 비목을 구분해 확인합니다.', ['gumi_expo'],
        candidate={'cities': ['구미시', '경산시', '김천시', '칠곡군', '상주시', '성주군', '경북 기타'], 'schedule': '상시 접수 표기 · 잔여 예산 확인'}, status='박람회 참가비 지원'),
    row('western-rnd-hiring', '경상북도', '경북 서부권 융합 R&D 인재 정착 5차', '구미전자정보기술원', ['new', 'hiring'],
        '신규채용 인력이 참여하는 기업 R&D 프로젝트의 과제비 1,500만 원(공급가액) 지원입니다. 개인 급여 하한·상한과 직접비 인건비 인정은 해당 회차 세부 기준을 확인합니다.',
        '채용일 기준 만 45세 이하 이공계 전문학사 이상 신규 인력 요건이 있습니다. 5차 회차의 접수는 마감됐으며 후속 모집 시 새 공고의 조건을 사용합니다.', ['gumi_rnd_jobs'],
        candidate={'cities': ['구미시', '김천시', '칠곡군', '상주시', '성주군'], 'deadline': '2026-07-24'},
        status='신규 인력의 채용·학위 요건 확인', excluded_grades=['hs']),
]


def candidate_fit(criteria, profile):
    checks = []
    if criteria.get('cities'):
        city = profile.get('city')
        checks.append(city in criteria['cities'] if city else None)
    if criteria.get('industries'):
        industries = profile.get('industries')
        checks.append(bool(set(industries) & set(criteria['industries'])) if industries else None)
    if criteria.get('min_staff'):
        staff = profile.get('staff')
        checks.append(int(staff) >= criteria['min_staff'] if staff else None)
    if False in checks:
        return '입력 조건과 다름'
    if None in checks or not checks:
        return '회사 조건 추가 확인'
    return '공개 공고와 입력 조건 일부 일치 · 세부 요건 확인'


def lookup(*, agency='', program='', grade='', role='', scope='all', profile=None):
    profile = profile or {}
    results = []
    for item in RULES:
        if (agency and agency != item['agency']) or (program and program != item['id']):
            continue
        if role and role not in item['roles']:
            continue
        candidate = item.get('candidate')
        fit = candidate_fit(candidate, profile) if candidate else None
        if scope == 'active' and item['id'] not in profile.get('projects', []):
            continue
        if scope == 'candidates' and (not candidate or fit == '입력 조건과 다름'):
            continue
        status = item.get('role_status', {}).get(role, item['status'])
        if grade in item.get('excluded_grades', ()):
            status = '공고의 학위 요건 미충족'
        result = {**item, 'status': status, 'sources': [SOURCES[ref] for ref in item['refs']]}
        if fit:
            result['company_fit'] = fit
        results.append(result)
    return results


def main():
    parser = argparse.ArgumentParser(description='회사 수행·후보 과제 인건비 근거 조회')
    parser.add_argument('--agency', choices=sorted({r['agency'] for r in RULES}))
    parser.add_argument('--program', choices=[r['id'] for r in RULES])
    parser.add_argument('--grade', choices=GRADES)
    parser.add_argument('--role', choices=ROLES)
    parser.add_argument('--scope', choices=('all', 'active', 'candidates'), default='all')
    parser.add_argument('--profile', type=Path, help='회사 조건과 수행 과제 ID가 있는 로컬 JSON')
    args = parser.parse_args()
    options = vars(args).copy()
    if args.profile:
        try:
            options['profile'] = json.loads(args.profile.read_text(encoding='utf-8-sig'))
        except (OSError, ValueError) as exc:
            parser.error(f'회사 프로필을 읽을 수 없습니다. {exc}')
    result = {'checked_on': PORTFOLIO_AS_OF, 'results': lookup(**options)}
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()

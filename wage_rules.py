"""2026년 정부지원사업 인건비 기준 조회. Python 3.10 이상, 외부 패키지 없음."""

import argparse
import json
from pathlib import Path

AS_OF = '2026-11-17'
GRADES = {'hs': '고졸', 'associate': '전문학사', 'bachelor': '학사', 'master': '석사', 'doctor': '박사'}
ROLES = {'employee': '직원·참여연구자', 'new': '신규채용 연구자', 'owner': '개인사업자 대표',
         'student': '학생연구자', 'contract': '학술연구용역 참여자', 'hiring': '채용지원 대상',
         'dispatch': '파견 연구자', 'qualified': '연구전담요원 등록'}


def source(title, date, section, url):
    return {'title': title, 'date': date, 'section': section, 'url': url}


SOURCES = {
    'wage': source('최저임금위원회 연도별 최저임금', '2025-08-05 고시 · 2026-01-01~12-31 적용', '2026년 시간급과 월 209시간 환산', 'https://www.minimumwage.go.kr/minWage/policy/decisionMain.do'),
    'rd': source('국가연구개발사업 연구개발비 사용 기준 제2026-38호', '2026-05-06 시행', '제2·6·7·21·39·40·48·49·57·65·73·74·89·91조', 'https://www.law.go.kr/admRulInfoP.do?admRulSeq=2100000278740'),
    'mss': source('2026년 중소기업기술개발 지원사업 관리지침', '2026-10-23 시행 · 첨부 본문 부칙 확인', '9. 다. 1) 직접비 인건비 가)~사), 14. 다. 2) 불인정 기준 및 부칙', 'https://research.uos.ac.kr/node/8940'),
    'mss_order': source('중소기업기술개발 지원사업 운영요령 제2026-6호', '2026-01-21 시행', '제14·19·21·22조 및 부칙', 'https://www.law.go.kr/admRulLsInfoP.do?admRulSeq=2100000273462'),
    'earnings': source('지표누리 한국의 사회지표 월평균 임금', '2025년 연간 통계 · 2026-11-17 열람', '상용근로자 임금총액 4,472천 원, 고용노동부 사업체노동력조사', 'https://www.index.go.kr/unity/potal/eNara/sub/showStblGams3.do?freq=Y&idx_cd=F0125&period=N&stts_cd=F012501'),
    'research_hire': source('중기부 2026년 중소기업 연구인력지원사업 제2026-69호', '2026-02-04 공고', '붙임 시행계획 2. 내역사업별 지원계획 신진·고경력·공공연 파견', 'https://www.mss.go.kr/site/smba/ex/bbs/View.do?bcIdx=1065325&cbIdx=310&parentSeq=1065325'),
    'industrial': source('산업기술혁신사업 공통 운영요령 제2024-218호', '2024-12-30 시행 · 2026-11-17 현행 공개본 확인', '제20조, 별표 4·5', 'https://www.law.go.kr/LSW/admRulLsInfoP.do?admRulSeq=2100000251982'),
    'industrial_case': source('산업통상부 민군융합핵심소재자립화기술개발 제2026-374호', '2026-05-26 공고', '인건비 현금 산정 및 기술분류 조건', 'https://www.iris.go.kr/contents/retrieveBsnsAncmView.do?ancmId=021796&bsnsAncmSn=1&bsnsYyDetail=2026&chngRcveDeFro=2026%2F06%2F02&chngRcveDeTo=2026%2F06%2F26&sorgnBsnsCd=S051592'),
    'ict': source('과기정통부 AI반도체 K-클라우드 기술개발 제2026-0444호', '2026-04-10 회차 공고', '영리기관 인건비 현금계상과 청년 의무채용', 'https://www.iris.go.kr/contents/retrieveBsnsAncmView.do?ancmId=019748&bsnsAncmSn=3&bsnsYyDetail=2026&chngRcveDeFro=2026%2F04%2F10&chngRcveDeTo=2026%2F04%2F23&sorgnBsnsCd=S049922'),
    'start': source('중기부 2026년 예비창업패키지 모집공고', '2026-02-27 게시 · 해당 회차', '붙임 사업화 자금 집행 비목 인건비', 'https://www.mss.go.kr/site/smba/ex/bbs/View.do?bcIdx=1065929&cbIdx=310&parentSeq=1065929'),
    'kocca': source('한국콘텐츠진흥원 지역 대표 글로컬 콘텐츠 제작·재투자 지원 추천기업 모집', '2026-03-17 공고 · 해당 협약기간', '지원금 사용범위 및 대표자 자부담', 'https://welcon.kocca.kr/ko/info/business/1957322'),
    'youth': source('고용노동부 2026년 청년일자리도약장려금 사업운영 지침', '2026-10-22 개정본 게시 · 2026년 채용분', '수도권 유형 Ⅱ 지원대상·Ⅳ 지원내용 및 비수도권 유형', 'https://www.moel.go.kr/news/notice/noticeView.do?bbs_seq=20261000802'),
    'work24': source('고용24 청년일자리도약장려금 제도안내', '2026년 사업 · 2026-11-17 열람', '지원내용, 지원자격 및 채용 후 예외 신청', 'https://www.work24.go.kr/cm/c/f/1100/selecSystInfo.do?currentPageNo=1&recordCountPer=10&systClId=SC00000117&systId=SI00000318'),
    'koita': source('기업부설연구소법 시행규칙 과기정통부령 제163호', '2026-02-01 시행', '제2조 제4항 제2·4·5·6호, 제5항 및 제6항', 'https://www.law.go.kr/lsLinkCommonInfo.do?lspttninfSeq=198229'),
    'contract': source('재정경제부 2026년 학술연구용역 인건비 기준단가', '2026-01-14 게시 · 2026년 기준', '예정가격작성기준 별표 5의 22일·참여율 50% 기준단가', 'https://www.mofe.go.kr/lw/denm/detailTbDenmView.do?menuNo=7090100&searchBbsId1=MOSFBBS_000000000119&searchNttId1=MOSF_000000000076494'),
    'contract_rule': source('재정경제부 예정가격작성기준 계약예규 제171호', '2026-08-25 시행', '제23조·제26조 및 별표 5', 'https://www.law.go.kr/admRulLsInfoP.do?admRulSeq=2100000284228'),
    'local_contract': source('행정안전부 지방자치단체 입찰 및 계약집행기준 제395호', '2026-11-06 시행', '제2장 제5절 제4관 및 별표 2, 2026년 단가', 'https://www.law.go.kr/admRulLsInfoP.do?admRulSeq=2100000287646'),
    'local_jb': source('전북테크노파크 혁신성장 R&D+ 1차 제2026-0048호', '2026-03-16 기업마당 게시 · 해당 회차', '첨부 공고 13쪽 인건비, 승인 산출표 확인', 'https://www.bizinfo.go.kr/sii/siia/selectSIIA200Detail.do?pblancId=PBLN_000000000119510'),
    'local_gb': source('경북테크노파크 2026년 미래차 부품 기술융합 지원', '2026-02-26 기업마당 게시 · 해당 회차', '공고 첨부 사업비 인건비', 'https://www.bizinfo.go.kr/sii/siia/selectSIIA200Detail.do?pblancId=PBLN_000000000118921'),
}
MIN_WAGE_MONTH = 2_156_880
OWNER_REFERENCE = 4_472_000
NEW_HIRE_MIN = {'associate': [3200, 3500, 3800], 'bachelor': [3200, 3500, 3800],
                'master': [4100, 4500, 4900], 'doctor': [5000, 5500, 6000]}
SENIOR_EXPERIENCE = {'associate': 16, 'bachelor': 14, 'master': 10, 'doctor': 5}
STUDENT_FLOOR = {'associate': 1_300_000, 'bachelor': 1_300_000, 'master': 2_200_000, 'doctor': 3_000_000}
CONTRACT_RATE = {'책임연구원': 3_783_728, '연구원': 2_901_312, '연구보조원': 1_939_429, '보조원': 1_454_621}


def row(key, agency, name, organization, roles, amount, cash, refs, **extra):
    return dict(id=key, agency=agency, name=name, organization=organization, roles=roles,
                amount=amount, cash=cash, refs=refs, **extra)


RULES = [
    row('minimum-wage', '고용노동부', '2026년 최저임금', '근로계약을 맺은 근로자', ['employee', 'new', 'hiring'],
        '시간당 10,320원. 월 209시간 환산 최저 2,156,880원. 임금 상한은 이 고시에서 정하지 않는다.',
        '근로계약 기준. 과제 재원 인정은 해당 사업 기준에 따름.', ['wage']),
    row('national-company', '과학기술정보통신부', '국가 R&D 공통 기업 기준', '영리 연구개발기관', ['employee', 'new'],
        '실제 월 급여와 과제별 계상률로 계산. 학위별 고정 하한·상한 없음. 전체 과제 계상액의 상한은 원칙적으로 월 급여 범위.',
        '중소·중견 신규채용(공고 전 6개월 포함), 신고 전문연구사업자, 국가소유 성과·기존 인력·대기업 등 소관 부처가 인정한 유형. 기존 인력은 인정 근거 없으면 현물 요건 검토.', ['rd']),
    row('national-college', '과학기술정보통신부', '국가 R&D 대학 기준', '대학·산학협력단 및 전문생산기술연구소 외 기타 비영리', ['employee'],
        '소속·원소속기관의 실제 월 급여 또는 무소속자의 연구참여계약 기준. 일반 직원의 학위별 고정액 없음.',
        '참여연구자·연구근접지원인력 현금 가능. 교원·공무원·영리기관 임직원 제한과 강사·겸임·초빙교원·부처 인정 등 단서 확인.', ['rd']),
    row('national-institute', '과학기술정보통신부', '국가 R&D 정부출연기관 기준', '정부출연기관 및 전문생산기술연구소', ['employee'],
        '실제 연 급여 기준. 참여연구자 연평균 계상 상한은 130%로 관리하되 개인 지급 상한은 기준 연 급여. 연구근접지원인력 연평균 100%.',
        '연구자·연구근접지원인력 현금 가능. 교원·공무원·영리기관 임직원 제한과 법정 단서 확인.', ['rd']),
    row('student', '과학기술정보통신부', '국가 R&D 학생인건비', '대학·출연기관 등 해당 학생인건비 적용기관', ['student'],
        '재학 중인 과정이 기준이다. 전문학사·학사 월 130만 원, 석사 월 220만 원, 박사 월 300만 원 이상으로 기관 기준 설정. 통합과정은 기관 기준.',
        '학생 신분과 연구참여확약서 확인. 기관기준과 지급률을 적용하며 실제 지급액에는 10% 관리기준과 타 기관 지급에 따른 단서가 있음.', ['rd'], student_floor=STUDENT_FLOOR),
    row('mss-rd', '중소벤처기업부', '중소기업기술개발 R&D', '중소기업 등 협약상 수행기관', ['employee', 'new'],
        '급여대장과 과제 참여기간 기준. 학위별 공통 최저액·최고액 없음. 신규인력 현금은 인정되는 인건비 범위까지.',
        '신규채용은 공고 전 6개월 이내 및 개발종료일까지, 반복 접수는 2회차부터 접수공고일 기준 확인. 기존 인력은 지정 기술분야, 전문연구사업자, 접수 마감일 기준 창업 7년 미만·신산업 창업 10년 이내, 육아 시간선택제 여성연구원, 사업별 인정 유형. 10월 23일 전 협약은 원칙적으로 협약 당시 규정.', ['mss', 'mss_order', 'rd'], agreement_cutoff='2026-10-23'),
    row('mss-owner', '중소벤처기업부', '중소기업기술개발 R&D 개인사업자 대표', '개인사업자 대표인 참여연구자', ['owner'],
        '전년도 종합소득세 신고 기준. 무소득 또는 비교 금액 이하이면 최신 연도 상용근로자 월평균 임금총액 적용. 2025년 기준 통계 월 4,472,000원. 해당 액수는 과제 계상 기준액이다.',
        '별도 현금 인정 요건과 협약 확인. 10월 23일 전 협약은 원칙적으로 협약 당시 규정.', ['mss', 'earnings'], agreement_cutoff='2026-10-23'),
    row('new-research-hire', '중소벤처기업부', '신진 연구인력 채용지원', '기업부설연구소·연구개발전담부서 보유 중소기업', ['hiring'],
        '전문학사·학사 3,200/3,500/3,800만 원, 석사 4,100/4,500/4,900만 원, 박사 5,000/5,500/6,000만 원의 연차별 최소 계약연봉. 계약연봉 상한은 별도 표기 없음.',
        '정규직·학위·경력·연령 등 충족 시 고정 지원. 50% 상당액에는 내일채움공제 또는 중기부 계약학과 지원 요건이 적용됨.', ['research_hire'], minimum_contract=NEW_HIRE_MIN),
    row('senior-research-hire', '중소벤처기업부', '고경력 연구인력 채용지원', '기업부설연구소·연구개발전담부서 보유 중소기업', ['hiring'],
        '공고상 별도 계약연봉 범위 없음. 정부지원액은 적격 세전 연봉의 절반, 1명당 연 최고 5,000만 원, 최대 3년.',
        '실제 정규직 계약과 학위 취득 후 연구개발 경력을 증빙. 제조AI 공고 예외 대상은 신진과 고경력을 각각 1명 지원 가능.', ['research_hire'], min_experience=SENIOR_EXPERIENCE),
    row('public-dispatch', '중소벤처기업부', '공공연 연구인력 파견지원', '협약 요건을 충족한 중소기업과 공공연구기관', ['dispatch'],
        '개별 파견기관 연봉 기준. 최초 3년 이내 연봉의 50%, 정규직 채용 등 추가연장 요건 충족 시 연장 3년간 60%. 공고상 공통 원화 상·하한 없음.',
        '공공연 파견기관의 인력 매칭과 승인 필요. 석·박사 또는 동등 자격 등 공고 요건 확인.', ['research_hire']),
    row('industrial-rd', '산업통상부', '산업기술혁신사업 R&D', '기업·대학·연구기관 협약 수행기관', ['employee', 'new'],
        '공통 대학·기업 월 급여 또는 출연연 연 급여 기준. 학위별 정액 없음. 위기지역 예외의 상한은 적용 정부지원연구개발비의 절반으로 사업비에 연동.',
        '제2026-374호 사례. 신규 채용액 범위 기존 인력 연동, 지정 SW·설계 등 평가 인정, 창업 초기 중소기업, 전문연구사업자, 시간선택제 여성연구원, 산업디자인전문회사, 산업위기지역.', ['industrial', 'industrial_case']),
    row('ict-rd', '과학기술정보통신부', 'ICT R&D K-클라우드 공고 사례', '중소·중견기업 등 제2026-0444호 수행기관', ['employee', 'new'],
        '실제 급여 기준. 학위별 정액 없음. 기존 인력 연동 현금의 최대액은 조건을 충족한 신규 인력의 해당 연도 현금 인건비.',
        '신규 현금이 연차별 기관 인건비(현금+현물)의 30% 이상일 때 같은 금액까지 기존 인력 현금 산정. 미달 시 연동 금액 전액 불인정. 전문연구사업자·창업기업·ICT 기술분야 등 별도 요건 공고 참조.', ['ict', 'rd']),
    row('startup', '중소벤처기업부', '예비창업패키지', '창업진흥원·해당 주관기관 사업화', ['employee', 'new'],
        '과제에 직접 투입되는 채용 예정 직원의 근로계약상 급여. 공고 인건비 항목에 학위별 원화 기준표 없음.',
        '근로계약에 따라 지급. 신청자의 배우자·직계존비속 인건비 편성 제한.', ['start']),
    row('content', '문화체육관광부', '지역 대표 글로컬 콘텐츠 제작·재투자', '한국콘텐츠진흥원 해당 사업', ['employee', 'owner'],
        '협약기간 내 제작·해외유통 참여 인력 급여. 공개 공고에 학위별 급여 범위 없음.',
        '대표자 직접 참여 시 자부담금으로만 인정. 협약체결일 이전 지출은 총사업비 산정 불가.', ['kocca']),
    row('jb', '전북특별자치도', '혁신성장 R&D+ 1차', '전북테크노파크 공고 제2026-0048호', ['employee', 'new', 'student'],
        '기업 신규+기존 현금 합계 최대 2,470만 원. 대학·출연연과 학생인건비는 공고 각 항목의 도지원금 한도 확인.',
        '신규채용 기준일·지원금 규모 조건 충족 필요. 기존 인력 연동 문구와 예시가 달라 기존 인력의 개별 한도는 전문기관 확인 후 산정. 재입사자는 신규 제외.', ['local_jb']),
    row('gb', '경상북도', '미래차 부품 기술융합', '경북테크노파크 해당 사업', ['employee', 'new'],
        '과제 급여 기준. 통합 학위별 금액표 없음. 승인된 세부 사업비 기준 확인.',
        '기존 인력은 현물. 신규 인력에 한해 현금 계상 가능.', ['local_gb']),
    row('youth-seoul', '고용노동부', '청년일자리도약장려금 수도권', '수도권 우선지원대상기업', ['hiring'],
        '최저임금 준수·월평균 급여 450만 원 이하(채용 근로조건). 기업지원 최고 월 60만 원, 1년 720만 원. 6개월 고용유지 필요.',
        '고졸 이하가 취업애로 요건의 하나. 대학 재학·휴학자는 해당 고졸 유형 제외. 학위 보유자는 다른 취업애로 요건 검토. 동일 신규 인력에 대한 타 정부 인건비 지원은 원칙 제외, 월 60만 원 미만이면 차액 지원 규정 확인.', ['youth', 'work24'], youth_cap=4_500_000),
    row('youth-local', '고용노동부', '청년일자리도약장려금 비수도권', '비수도권 우선지원대상기업·중견기업', ['hiring'],
        '최저임금 준수·월평균 급여 450만 원 이하(채용 근로조건). 기업지원 최고 월 60만 원, 1년 720만 원. 지역별 청년 근속 인센티브는 별도.',
        '고졸 여부와 관계없이 근로조건과 청년·기업 요건 확인. 타 정부 신규 인력 인건비 지원 시 원칙 제외, 월 60만 원 미만 차액 규정 확인.', ['youth', 'work24'], youth_cap=4_500_000),
    row('koita-qualification', '과학기술정보통신부', '기업부설연구소 연구전담요원 등록', '기업부설연구기관 및 연구개발전담부서', ['qualified'],
        '연구전담요원 자격 기준. 별도 임금 하한·상한 또는 지원금 규정이 아님.',
        '고졸도 기사 이상 기술자격 경로가 있다. 중소기업은 산업기사+2년, 기능사+4년, 해당 특성화고·마이스터고 졸업+연구개발 4년 경로가 있다. 학위·업종별 세부 요건 참조.', ['koita']),
    row('central-contract', '재정경제부', '국가 발주 학술연구용역', '국가기관 발주 계약', ['contract'],
        '월 22일·참여율 50% 기준 책임연구원 3,783,728원, 연구원 2,901,312원, 연구보조원 1,939,429원, 보조원 1,454,621원. 등급과 참여기간에 따라 산정.',
        '예정가격 기준단가. 발주처 직급·업무 및 자격을 대조. R&D 현물 인정 규정과 별개.', ['contract', 'contract_rule'], contract_rates=CONTRACT_RATE),
    row('municipal-contract', '행정안전부', '지자체 발주 학술연구용역', '지방자치단체 발주 계약', ['contract'],
        '월 22일·참여율 50% 기준 책임연구원 3,783,728원, 연구원 2,901,312원, 연구보조원 1,939,429원, 보조원 1,454,621원. 등급과 참여기간에 따라 산정.',
        '행정안전부 예규의 예정가격 기준단가. 발주처 직급·업무 및 자격을 대조.', ['local_contract'], contract_rates=CONTRACT_RATE),
]


def lookup(*, agency='', program='', grade='', role='', course='', year=1,
           salary=None, agreement_date='', contract_rank=''):
    results = []
    for item in RULES:
        if agency and agency != item['agency'] or program and program != item['id']:
            continue
        if role and role not in item['roles']:
            continue
        status = '공고·협약 및 개인 증빙 확인'
        value = None
        key = item['id']
        if agreement_date and item.get('agreement_cutoff', '') > agreement_date:
            status = '이전 협약 적용본 확인 필요'
        elif key in ('new-research-hire', 'senior-research-hire') and grade == 'hs':
            status = '공고의 학위 요건 미충족'
        elif key == 'new-research-hire' and grade:
            minimum = item['minimum_contract'][grade][year - 1] * 10_000
            value = {'연차별 최소 계약연봉': minimum, '기본 정부지원액': minimum * 4 // 10,
                     '추가조건 충족 시 정부지원 상한': minimum // 2}
            if salary is not None:
                status = '계약연봉 조건 충족 · 기타 요건 확인' if salary * 12 >= minimum else '최소 계약연봉 미달'
        elif key == 'senior-research-hire' and grade:
            status = f'학위 취득 후 연구개발 경력 {item["min_experience"][grade]}년 이상 필요'
            if salary is not None:
                value = {'입력 급여로 본 연간 지원 상한': min(salary * 6, 50_000_000)}
        elif key == 'student' and course:
            value = {'과정별 기관 계상기준 하한': STUDENT_FLOOR[course]}
        elif key == 'mss-owner':
            value = {'2025년 상용근로자 월평균 임금총액': OWNER_REFERENCE}
        elif key == 'minimum-wage':
            value = {'2026년 209시간 월 환산액': MIN_WAGE_MONTH}
        elif 'youth_cap' in item:
            if salary is not None and salary > item['youth_cap']:
                status = '월평균 급여 한도 초과'
            if key == 'youth-seoul' and grade == 'hs' and status == '공고·협약 및 개인 증빙 확인':
                status = '고졸 유형 검토 가능 · 채용 시 대학 재학·휴학 등 제외 확인'
        elif 'contract_rates' in item and contract_rank:
            value = {'월 기준단가(22일·참여율 50%)': item['contract_rates'][contract_rank]}
        results.append({**item, 'status': status, 'computed_krw': value,
                        'sources': [SOURCES[ref] for ref in item['refs']]})
    return results


def main():
    parser = argparse.ArgumentParser(description=f'{AS_OF} 한국 정부지원사업 인건비 기준 조회')
    parser.add_argument('--agency', choices=sorted({r['agency'] for r in RULES}), default='')
    parser.add_argument('--program', choices=[r['id'] for r in RULES], default='')
    parser.add_argument('--grade', choices=GRADES, default='', help='최종학력. hs/associate/bachelor/master/doctor')
    parser.add_argument('--role', choices=ROLES, default='')
    parser.add_argument('--course', choices=STUDENT_FLOOR, default='', help='현재 재학 중인 학생연구자 과정')
    parser.add_argument('--year', type=int, choices=(1, 2, 3), default=1)
    parser.add_argument('--salary', type=int, help='월 세전 원화. 채용사업별 산입 임금 기준 사용')
    parser.add_argument('--agreement-date', default='', help='해당 과제 협약일 YYYY-MM-DD')
    parser.add_argument('--contract-rank', choices=CONTRACT_RATE, default='')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    if args.salary is not None and args.salary < 0:
        parser.error('월 급여는 0원 이상이어야 합니다.')
    if args.agreement_date:
        from datetime import date
        try:
            args.agreement_date = date.fromisoformat(args.agreement_date).isoformat()
        except ValueError:
            parser.error('협약일을 YYYY-MM-DD로 입력하세요.')
    options = vars(args).copy()
    json_output = options.pop('json')
    results = lookup(**options)
    if json_output:
        print(json.dumps({'checked_on': AS_OF, 'results': results}, ensure_ascii=False, indent=2))
        return
    print(f'자료 확인일 {AS_OF} · {len(results)}개 기준')
    for record in results:
        print(f'\n{record["agency"]} / {record["name"]} · {record["status"]}')
        print(record['amount'])
        for label, amount in (record['computed_krw'] or {}).items():
            print(f'{label} {amount:,}원')
        print(record['cash'])
        for item in record['sources']:
            print(f'{item["title"]} · {item["date"]} · {item["section"]}\n{item["url"]}')


if __name__ == '__main__':
    main()

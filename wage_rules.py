"""2026년 정부지원사업 인건비 기준 조회. Python 3.10 이상, 외부 패키지 없음.

이 파일이 데이터 원본이다. 웹 페이지(index.html)와 Word 보고서의 출처 번호 [S01]~는 모두 여기의 SOURCES를 따른다.
"""

import argparse
import json
import re
import sys

AS_OF = '2026-11-17'
VERSION = '2.0'
GRADES = {'hs': '고졸', 'associate': '전문학사', 'bachelor': '학사', 'master': '석사', 'doctor': '박사'}
COURSES = {'associate': '전문학사 과정', 'bachelor': '학사 과정', 'master': '석사 과정', 'doctor': '박사 과정'}
ROLES = {'employee': '직원·참여연구자', 'new': '신규채용 연구자', 'external': '외부·무소속 참여연구자',
         'owner': '개인사업자 대표', 'student': '학생연구자', 'contract': '학술연구용역 참여자',
         'hiring': '채용지원 대상', 'dispatch': '파견 연구자', 'qualified': '연구전담요원 등록'}


def src(org, title, doc_no, date, section, url, kind='1차'):
    return {'org': org, 'title': title, 'docNo': doc_no, 'date': date, 'section': section, 'url': url, 'kind': kind}


# 출처 번호는 분야별로 묶어 S01부터 매긴다. Word 보고서 부록 A와 같은 번호다.
SOURCES = {
    # 공통 임금
    'S01': src('최저임금위원회', '연도별 최저임금 결정현황', '', '2026년 적용 · 2027년 결정액 포함', '시간급, 월 209시간 환산',
               'https://www.minimumwage.go.kr/minWage/policy/decisionMain.do'),
    'S02': src('법제처', '최저임금법 및 시행령', '', '현행', '법 제5조제2항(수습 감액 요건·단순노무 제외), 시행령 제3조(감액 금액)',
               'https://www.law.go.kr/법령/최저임금법'),
    # 국가 R&D 공통
    'S03': src('법제처', '국가연구개발혁신법 시행령', '', '현행', '제19조·제20조·제26조, 별표 1·2',
               'https://www.law.go.kr/LSW/lsInfoP.do?lsId=013933'),
    'S04': src('과학기술정보통신부', '국가연구개발사업 연구개발비 사용 기준', '고시 제2026-38호', '2026-05-06 발령·시행',
               '제39조제5항(출연연 130%), 제40조제4항(학생 하한)·제10항(10%), 제48조제4·5항, 제49조, '
               '제57조, 제65조제4항(현금 예외)·제7항, 제26·73·74조, 제91조제5항',
               'https://www.law.go.kr/admRulInfoP.do?admRulSeq=2100000278740'),
    'S05': src('과학기술정보통신부', '연구개발비 사용 기준 개정안 행정예고', '공고 제2026-1017호', '2026-10-15 공고 · 2027-01-01 시행 예정',
               '연구수당 1인 지급 상한(제26조제6항 신설), 보안수당, 단계 간 잔액의 인건비 사용(제71조제3항)',
               'https://www.msit.go.kr/bbs/view.do?bbsSeqNo=84&mId=109&mPid=103&nttSeqNo=3186413&sCode=user'),
    'S06': src('과학기술정보통신부', '학생인건비 통합관리기관 목록', '공고 제2026-1033호', '2026-10-21 공고', '고시 제86조제1항에 따른 지정 기관',
               'https://www.msit.go.kr/bbs/view.do?bbsSeqNo=96&mId=310&mPid=121&nttSeqNo=3186636&sCode=user'),
    'S07': src('KISTEP', '국가연구개발혁신법 매뉴얼(2026년 7월 개정)', '', '2026-07-15 게시', '본권·부록·신구조문대비표',
               'https://www.kistep.re.kr/board.es?act=view&bid=0003&list_no=94788&mid=a10402000000'),
    # 중기부 기술개발
    'S08': src('중소벤처기업부', '중소기업기술개발 지원사업 운영요령', '고시 제2026-6호', '2026-01-21 시행', '제14·19·21·22조 및 부칙',
               'https://www.law.go.kr/admRulLsInfoP.do?admRulSeq=2100000273462'),
    'S09': src('중소벤처기업부', '중소기업기술개발 지원사업 관리지침', '', '2026-10-23 시행(같은 해 8-3 시행본도 있음)',
               '9. 다. 1) 직접비 인건비, 14. 다. 2) 불인정 기준, 부칙. 원문은 IRIS 자료실(2026-10-23 등록) 첨부',
               'https://research.uos.ac.kr/node/8940', kind='2차'),
    'S10': src('중소벤처기업부', '민관공동기술사업화 R&D(구매연계·상생협력) 제3차 시행계획 공고', '', '2026년', '주요 변경사항, 비목별 산정기준',
               'https://www.iris.go.kr/contents/retrieveBsnsAncmView.do?ancmId=021714'),
    'S11': src('중소벤처기업부', '표준공정 기반 공정최적화 기술개발사업 시행계획 공고', '공고 제2026-484호', '2026-07-30 공고',
               '붙임 주요 연구개발비 산정기준, 청년 의무채용',
               'https://www.iris.go.kr/contents/retrieveBsnsAncmView.do?ancmId=023077&ancmPrg=ancmIng'),
    'S12': src('통계청 지표누리', '월평균 임금(상용근로자 임금총액)', '', '2025년 연간 · 2026-11-17 열람',
               '상용근로자 임금총액(고용노동부 사업체노동력조사)',
               'https://www.index.go.kr/unity/potal/eNara/sub/showStblGams3.do?freq=Y&idx_cd=F0125&period=N&stts_cd=F012501'),
    # 중기부 연구인력
    'S13': src('중소벤처기업부', '2026년 중소기업 연구인력지원사업 공고', '공고 제2026-69호', '2026-02-04 공고',
               '붙임 내역사업별 지원계획(신진·고경력·공공연 파견), 기준연봉·지원비율',
               'https://www.mss.go.kr/site/smba/ex/bbs/View.do?bcIdx=1065325&cbIdx=310&parentSeq=1065325'),
    'S14': src('경기도일자리재단', '2026년 중소기업 연구인력지원사업(파견) 11월 공고 안내', '', '2026-11 게시', '공공연 파견 연봉 지원·모집 조건',
               'https://job.gg.go.kr/entSprt/detail.do?seq=5218', kind='2차'),
    'S15': src('과학기술정보통신부', '기업부설연구소법 시행규칙', '과기정통부령 제163호', '2026-02-01 시행', '제2조 제4항~제6항(연구전담요원 자격)',
               'https://www.law.go.kr/lsLinkCommonInfo.do?lspttninfSeq=198229'),
    # 산업통상부
    'S16': src('산업통상부(발령 당시 산업통상자원부)', '산업기술혁신사업 공통 운영요령', '고시 제2024-218호', '2024-12-30 시행',
               '제20조제2항(최소 계상률 10%)·제24조, 별표 4(현금 인정 기술분야)·별표 5(연구개발비 산정기준)',
               'https://www.law.go.kr/LSW/admRulLsInfoP.do?admRulSeq=2100000251982'),
    'S17': src('산업통상부', '2026년 민군융합핵심소재자립화기술개발사업 신규지원 대상과제 공고', '공고 제2026-374호', '2026-05-26 공고',
               '인건비 현금 산정기준, 청년인력 채용',
               'https://www.iris.go.kr/contents/retrieveBsnsAncmView.do?ancmId=021796&bsnsAncmSn=1&bsnsYyDetail=2026'
               '&chngRcveDeFro=2026%2F06%2F02&chngRcveDeTo=2026%2F06%2F26&sorgnBsnsCd=S051592'),
    'S18': src('산업통상부', '산업기술혁신사업 공통 운영요령 개정안 행정예고', '공고 제2026-558호', '2026-09-01 행정예고 · 11-17 현재 미고시',
               '최소 인건비계상률 규정(제20조제2항·별표 6) 삭제 등',
               'https://www.motir.go.kr/kor/article/ATCLa6723dc7b/519/view?pageIndex=1'),
    # 과기정통부 ICT
    'S19': src('과학기술정보통신부', '2026년 AI반도체를 활용한 K-클라우드 기술개발 신규지원 대상과제 공고', '공고 제2026-0444호', '2026-04-10 공고',
               '영리기관 인건비 현금계상, 청년 의무채용',
               'https://www.iris.go.kr/contents/retrieveBsnsAncmView.do?ancmId=019748&bsnsAncmSn=3&bsnsYyDetail=2026'
               '&chngRcveDeFro=2026%2F04%2F10&chngRcveDeTo=2026%2F04%2F23&sorgnBsnsCd=S049922'),
    # 창업·콘텐츠
    'S20': src('창업진흥원', '중소기업창업 지원사업 통합관리지침(제14차 개정)', '', '2026-01-22 최종수정', '사업비 집행 기준',
               'https://www.k-startup.go.kr/user/board/webRFRR_view_reference.do?id=172153&schM=view'),
    'S21': src('중소벤처기업부', '2026년 예비창업패키지 예비창업자 모집공고', '공고 제2026-142호', '2026-02-27 공고 · 수정공고 제2026-143호·제2026-207호',
               '사업화 자금 집행 비목 인건비',
               'https://www.mss.go.kr/site/smba/ex/bbs/View.do?bcIdx=1065929&cbIdx=310&parentSeq=1065929'),
    'S22': src('한국콘텐츠진흥원', '2026년 지역 대표 글로컬 콘텐츠 제작·재투자 지원 추천기업 모집 공고', '', '2026-03-17 공고',
               '지원금 사용범위, 대표자 인건비 재원', 'https://welcon.kocca.kr/ko/info/business/1957322'),
    # 지자체·테크노파크
    'S23': src('경북테크노파크', '2026년 미래차 부품 기술융합 지원 사업 공고', '', '2026-02-26 기업마당 게시', '첨부 공고문(hwp)의 사업비·인건비',
               'https://www.bizinfo.go.kr/sii/siia/selectSIIA200Detail.do?pblancId=PBLN_000000000118921'),
    'S24': src('전북테크노파크', '2026년 1차 혁신성장 R&D+ 지원사업 모집 공고', '공고 제2026-0048호', '2026-03-09 공고 · 03-16 기업마당 게시',
               '첨부 공고 [참고2] 사업비 편성기준(13쪽) 인건비·현금 한도',
               'https://www.bizinfo.go.kr/sii/siia/selectSIIA200Detail.do?pblancId=PBLN_000000000119510'),
    'S25': src('행정안전부', '지방보조금 관리기준', '예규 제378호', '2026-08-18 시행', '보조사업 교부조건·집행 기준',
               'https://www.law.go.kr/LSW/admRulInfoP.do?admRulSeq=2100000284062&chrClsCd=010201'),
    # 고용
    'S26': src('고용노동부', '2026년 청년일자리도약장려금 사업운영 지침(10월 개정)', '', '2026-10-22 게시',
               '지원대상·지원내용, 수도권·비수도권 유형, 중복지원 제한. 10월 개정은 장기근속인센티브 지급 방법',
               'https://www.moel.go.kr/news/notice/noticeView.do?bbs_seq=20261000802'),
    'S27': src('고용24', '청년일자리도약장려금 제도안내', '', '2026년 사업 · 2026-11-17 열람', '지원내용, 지원자격, 채용 후 신청 예외',
               'https://www.work24.go.kr/cm/c/f/1100/selecSystInfo.do?currentPageNo=1&recordCountPer=10'
               '&systClId=SC00000117&systId=SI00000318'),
    # 학술연구용역
    'S28': src('재정경제부(2026-01-02 출범, 구 기획재정부)', '2026년 학술연구용역 인건비 기준단가', '', '2026-01-14 게시',
               '월 22일·참여율 50% 기준 직급별 단가(2025년 소비자물가 2.1% 반영)',
               'https://www.mofe.go.kr/lw/denm/detailTbDenmView.do?menuNo=7090100&searchBbsId1=MOSFBBS_000000000119'
               '&searchNttId1=MOSF_000000000076494'),
    'S29': src('재정경제부', '(계약예규) 예정가격작성기준', '계약예규 제171호', '2026-08-25 시행', '제23조·제26조, 별표 5',
               'https://www.law.go.kr/admRulLsInfoP.do?admRulSeq=2100000284228'),
    'S30': src('행정안전부', '지방자치단체 입찰 및 계약집행기준', '예규 제395호', '2026-11-06 시행', '제2장 별표 2(학술연구용역 단가)',
               'https://www.law.go.kr/admRulLsInfoP.do?admRulSeq=2100000287646'),
    'S31': src('국가기술표준원', '2026년 연구용역 입찰공고 첨부(원가계산서 작성요령)', '공고 제2026-68호', '2026년', '100% 환산 단가 표기 사례',
               'https://www.g2b.go.kr/pn/pnp/pnpe/UntyAtchFile/downloadFile.do?bidPbancNo=R26BK01368127&bidPbancOrd=000'
               '&fileSeq=2&fileType=&prcmBsneSeCd=03'),
    'S32': src('국립환경과학원', '연구용역과제 계약 및 정산규정', '', '현행', '참여인력 직급별 자격·기능수준',
               'https://www.law.go.kr/LSW/admRulInfoP.do?admRulSeq=2100000280926'),
    # 검토 과정에서 추가한 1차 출처
    'S33': src('법제처', '정부조직법 개정이유(법률 제21065호)', '법률 제21065호', '2025-10-01 공포',
               '산업통상부 2025-10-01, 재정경제부·기획예산처 2026-01-02 시행',
               'https://www.law.go.kr/LSW/lsRvsRsnListP.do?lsId=001720&chrClsCd=010202&lsRvsGubun=all'),
    'S34': src('중소기업기술정보진흥원(SMTECH)', '2026년 신진 연구인력 채용지원 공고 상세', '공고 제2026-69호', '2026-02-04 공고',
               '지원대상·지원내용(기준연봉, 40%·50%, 기업별 1명)',
               'https://www.smtech.go.kr/front/ifg/no/notice02_detail.do?buclYy=2026&ancmId=S02834&buclCd=S6042'
               '&dtlAncmSn=1&schdSe=MO5005&aplySn=1'),
    'S35': src('중소기업기술정보진흥원(SMTECH)', '2026년 공공연 연구인력 파견지원 11월 공고 상세', '', '2026-11 공고',
               '파견 연봉 50%, 정규직 채용 시 60%',
               'https://www.smtech.go.kr/front/ifg/no/notice02_detail.do?buclYy=&ancmId=S02847&buclCd=S6041'
               '&dtlAncmSn=11&schdSe=MO5005&aplySn=1'),
    'S36': src('한국산업기술진흥협회(KOITA)', '고경력 연구인력 채용지원 안내', '', '2026-11-17 열람', '연봉 50%, 연간 최대 5,000만 원',
               'https://www.koita.or.kr/conts/102002006000000.do'),
    'S37': src('고용노동부', '2027년 적용 최저임금 고시', '고시 제2026-60호', '2026-08-05 고시', '2027-01-01부터 시간급 10,700원',
               'https://www.moel.go.kr/info/lawinfo/instruction/view.do?bbs_seq=20260800150'),
}
# 웹 기준과 직접 연결되지 않고 보고서 본문에서만 인용하는 출처
DOC_ONLY_SOURCES = {'S02', 'S03', 'S05', 'S07', 'S18', 'S33'}

MIN_WAGE = {'2026': 10_320, '2027': 10_700}
MIN_WAGE_MONTH = MIN_WAGE['2026'] * 209
OWNER_REFERENCE = 4_472_000
NEW_HIRE_MIN = {'associate': [3200, 3500, 3800], 'bachelor': [3200, 3500, 3800],
                'master': [4100, 4500, 4900], 'doctor': [5000, 5500, 6000]}
SENIOR_EXPERIENCE = {'associate': 16, 'bachelor': 14, 'master': 10, 'doctor': 5}
SENIOR_CAP = 50_000_000
STUDENT_FLOOR = {'associate': 1_300_000, 'bachelor': 1_300_000, 'master': 2_200_000, 'doctor': 3_000_000}
CONTRACT_RATE = {'책임연구원': 3_783_728, '연구원': 2_901_312, '연구보조원': 1_939_429, '보조원': 1_454_621}
YOUTH = {'monthly': 600_000, 'yearly': 7_200_000, 'wage_cap': 4_500_000}
DEGREE = ['associate', 'bachelor', 'master', 'doctor']


def rec(key, agency, name, organization, roles, summary, amount, cash, refs, *, evidence=(), note='',
        status='현행', grades=None, keywords='', **extra):
    return dict(id=key, agency=agency, name=name, organization=organization, roles=list(roles), summary=summary,
                amount=amount, cash=cash, evidence=list(evidence), note=note, status=status, grades=grades,
                keywords=keywords, refs=list(refs), **extra)


RULES = [
    rec('minimum-wage', '고용노동부', '최저임금', '근로계약을 맺은 모든 근로자(학력 무관)', ['employee', 'new', 'hiring'],
        '2026년 시간당 10,320원 · 월 2,156,880원(209시간). 2027년 시간당 10,700원.',
        '2026.1.1.~12.31. 시간급 10,320원, 8시간 일급 82,560원, 월 209시간 환산 2,156,880원. '
        '2027.1.1.부터 시간급 10,700원, 월 환산 2,236,300원. 임금 상한은 정하지 않는다.',
        '근로계약 기준의 하한이다. 과제에서 얼마를 인정받는지는 해당 사업 기준에 따른다. '
        '1년 이상 근로계약의 수습 3개월 이내는 시간급의 90%까지 가능하나(법 제5조제2항, 시행령 제3조) 단순노무 직종은 감액할 수 없다.',
        ['S01', 'S37', 'S02'], evidence=['근로계약서(소정근로시간)', '임금명세서', '최저임금 산입범위 검토'],
        note='2027년 최저임금은 2026-08-05 고시됐다. 단시간·중도 채용은 소정근로시간과 유급시간으로 다시 환산한다.',
        keywords='시급 최저 월급 수습 2027'),
    rec('national-company', '과학기술정보통신부', '국가 R&D 공통 · 영리기관', '기업·공기업 등 영리 연구개발기관', ['employee', 'new'],
        '실제 월 급여 × 계상률 · 1인 월 총계상률 100% 이내 · 현금은 제65조제4항 예외에 해당할 때만.',
        '참여연구자별 월 단위로 실제 급여에 계상률을 곱해 계상한다. 학위별 고정 하한·상한은 없다. '
        '한 사람의 모든 과제 계상률 합계는 월 100% 이내다(제65조제7항).',
        '제65조제4항이 현금 계상 대상을 열거한다: ① 중소·중견기업이 신규 채용한 인력(채용일부터 과제 공고일까지 6개월 이내인 사람 포함) '
        '② 전문연구사업자 소속 ③ 중앙행정기관장이 인정하는 경우. 해당하지 않는 기존 인력은 현물 계상을 검토한다.',
        ['S04', 'S03'], evidence=['급여대장', '근로계약서·4대보험 가입 이력', '계상률 산출표', '현금 인정 근거 조항'],
        note='"기존 인력은 원칙적으로 현물"은 고시 문구가 아니라 공고문에서 쓰는 표현이다.',
        keywords='기업 현물 현금 계상률 신규채용 제65조'),
    rec('national-college', '과학기술정보통신부', '국가 R&D 공통 · 대학·기타 비영리', '대학·산학협력단, 제57조의 기타 비영리기관',
        ['employee', 'external'],
        '실제 월 급여(무소속자는 참여계약) × 계상률 · 월 총계상률 100% 이내.',
        '소속 또는 원소속기관의 실제 월 급여, 무소속자는 연구참여계약서 금액을 기준으로 한다. 일반 직원의 학위별 고정액은 없다. '
        '명칭에 연구원·센터가 들어가도 법적 기관 유형을 확인한다.',
        '참여연구자·연구근접지원인력은 현금 가능(제48조제4항). 대학 교원, 국공립 연구기관 공무원, 영리기관 임직원은 제한·단서가 있다.',
        ['S04'], evidence=['원소속기관 급여 확인서', '연구참여계약서', '연구근접지원인력 지정 자료'],
        keywords='산학협력단 비영리 연구근접지원인력 제48조 제57조'),
    rec('national-institute', '과학기술정보통신부', '국가 R&D 공통 · 정부출연기관', '정부출연기관, 전문생산기술연구소(제57조 준용)',
        ['employee'],
        '연 단위 · 참여연구자 연평균 130% 이내 · 개인 지급은 기준 연 급여까지.',
        '참여연구자(학생 제외) 연평균 총인건비계상률 130% 이내, 연구근접지원인력 연평균 100% 이내로 관리한다(제39조제5항). 계상률이 100%를 넘어도 '
        '개인에게 지급할 수 있는 인건비는 기준 연 급여까지다.',
        '참여연구자·연구근접지원인력 현금 가능. 교원·공무원·영리기관 임직원 제한과 기관 총액 관리 기준을 확인한다.',
        ['S04'], evidence=['기관 인건비 총액 관리 자료', '연 급여 기준표'], keywords='출연연 130% 연평균 제39조'),
    rec('external-researcher', '과학기술정보통신부', '국가 R&D 공통 · 외부 참여연구자', '타 기관 소속자, 무소속 참여연구자', ['external'],
        '원소속기관 급여 근거로 계상 · 계상 후 원소속기관에 통보 · 무소속은 참여계약서 기준.',
        '타 기관 소속자는 원소속기관의 급여 근거와 참여 확인서를 받아 계상한다. 원소속이 없는 사람은 연구참여계약서 금액을 쓴다.',
        '일회성 자문은 참여연구자 등록과 별개로 연구활동비의 전문가 활용비 요건을 본다. 영리기관의 연구지원인력은 간접비 기준이 적용된다.',
        ['S04'], evidence=['원소속기관 참여확인서·통보 기록', '연구참여계약서'], keywords='타기관 겸직 자문 무소속'),
    rec('student', '과학기술정보통신부', '국가 R&D 학생인건비', '대학·출연기관 등 학생인건비 적용기관', ['student'],
        '재학 과정별 월 하한: 학사(전문학사) 130만 원 · 석사 220만 원 · 박사 300만 원 이상으로 기관 기준 설정.',
        '현재 재학 중인 과정이 기준이다(최종학력 아님). 금액은 제40조제4항(대학은 제49조 준용)이며 2024-02-29 개정 이후 같다. '
        '기관 계상기준에는 4대보험 기관부담금·퇴직급여충당금을 넣지 않으며, '
        '같은 기관 안에서 학과·연구책임자별로 다른 기준을 둘 수 없다. 통합과정은 기관장이 정한다.',
        '학생별 지급액 합계를 과정별 고시 금액의 10% 이상으로 관리한다(제40조제10항, 월 총계상률 90% 초과 시 예외). 통합관리기관은 기관계정의 20% 이상 '
        '균등지급 노력 의무가 있다(제91조제5항). 같은 과제에서 동일인의 인건비와 학생인건비를 중복 계상할 수 없다.',
        ['S04', 'S06'], evidence=['재학·수료·연구생 등록 확인서', '연구참여확약서', '기관 학생연구자 지원규정'],
        note='졸업 후 직원으로 고용되면 근로계약·기관 급여 기준으로 바뀐다. 졸업일이 속한 달 말일까지 지급 가능(통합관리기관).',
        keywords='학생 대학원생 석사 박사 학사 확약서 통합관리', student_floor=STUDENT_FLOOR),
    rec('staff-change', '과학기술정보통신부', '참여 인력 교체·현금 인건비 변경', '국가 R&D 수행기관 공통', ['employee', 'new'],
        '영리기관 현금 인건비 총액 변경·신규 인력 현금 감액은 사전 승인 · 수정인건비 20% 한도 검토.',
        '현금 인건비 총액 변경 또는 신규인력 현금 인건비 감액은 중앙행정기관의 장 사전 승인 대상이다. 연도별 기관부담 연구개발비의 '
        '현금·현물 변경도 사전 승인 대상이다. 연구수당과 함께 바뀌면 제26조 수정인건비 산정 범위와 20% 한도를 검토한다.',
        '신청 접수 후 원칙적으로 15일 이내 승인 여부를 통보하며 연장될 수 있다. 신규 인력이 퇴사하면 연동된 기존 인력 현금액을 함께 재산정한다.',
        ['S04'], evidence=['인력별 변경 전후 산출표', '채용·퇴사 근거', '승인 공문', '시스템 참여인력 변경 이력'],
        keywords='퇴사 교체 승인 변경 제73조 제74조 제26조'),
    rec('mss-rd', '중소벤처기업부', '중소기업기술개발 R&D', '중소기업 등 협약상 수행기관', ['employee', 'new'],
        '실제 급여 × 참여기간 · 신규채용 현금 가능 · 기존 인력은 지정 요건 충족 시에만 현금.',
        '급여대장과 과제 참여기간을 기준으로 한다. 학위별 공통 최저·최고액은 없다. 신규 인력은 인정 인건비 범위까지 현금 계상 가능.',
        '신규채용: 공고일 전 6개월 이내부터 개발 종료일까지 채용(연 2회 이상 접수 사업은 2회차부터 접수공고일 기준). '
        '기존 인력 현금: 지정 기술분야, 전문연구사업자, 접수 마감일 기준 창업 7년 미만·신산업 창업 10년 이내, '
        '육아 시간선택제 여성연구원, 사업별 지정 유형. 민관공동 제3차는 창업기업 기존 인력 현금을 허용한다.',
        ['S09', 'S08', 'S04', 'S10'],
        evidence=['협약서와 적용 지침 버전', '근로계약·고용보험 취득일', '창업일·신산업 증빙', '전문연구사업자 신고증'],
        note='2026-10-23 이전에 체결한 협약은 원칙적으로 협약 종료까지 협약 당시 지침을 적용한다(관리지침 부칙, 재게시본 기준. '
             '같은 해 2026-08-03 시행본도 있으므로 협약에 편입된 버전을 확인).',
        keywords='중기부 기술개발 현금 현물 창업 신산업 전문연구사업자 시간선택제', agreement_cutoff='2026-10-23'),
    rec('mss-youth', '중소벤처기업부', '중기부 R&D 청년 의무채용(공정최적화 사례)', '표준공정 기반 공정최적화 기술개발 수행기업', ['new'],
        '정부지원연구개발비 5억 원당 청년 1명 이상 신규채용 · 초과 채용분은 기관부담 현금을 현물로 대체 가능.',
        '기업이 받는 정부지원연구개발비 합계가 5억 원 이상이면 5억 원당 청년 1명 이상 신규채용을 요구한다.',
        '의무 인원·청년 연령·고용 유지기간·미채용 조치는 협약 조항을 확인한다. 의무를 넘겨 추가 채용하면 해당 인건비 범위에서 '
        '기관부담 현금을 현물로 대체할 수 있다(공고에 명시된 사업).',
        ['S11', 'S09'], evidence=['채용 계획·실적', '고용보험 자격 이력'], status='확인 필요',
        note='공고 원문(hwp 첨부)과 대조하지 못했다. 다른 중기부 2026 R&D 공고에는 정부지원금 5억 원 이상 과제에 한해 '
             '5억 원당 청년(만 15~34세, 연구직 정규직) 1명 이상 채용·1년 이상 고용유지 조건이 있다.',
        keywords='청년 의무채용 5억'),
    rec('mss-owner', '중소벤처기업부', '중기부 R&D 개인사업자 대표', '개인사업자 대표인 참여연구자', ['owner'],
        '전년도 종합소득세 신고 기준 · 무소득·기준 이하이면 상용근로자 월평균 임금총액(2025년 4,472,000원).',
        '전년도 종합소득세 신고액을 기준으로 한다. 소득이 없거나 비교 기준 이하이면 최신 연도 상용근로자 월평균 임금총액을 적용한다. '
        '이 금액은 과제 계상 기준액이다.',
        '현금 계상은 별도 인정 요건과 협약을 확인한다.',
        ['S09', 'S12'], evidence=['종합소득세 신고서', '사업자등록증'], status='확인 필요',
        note='통계 수치(2025년 4,472천 원, 2024년 4,338천 원)는 확인했다. 2026-10-23 관리지침의 현재 문구는 원문과 대조하지 못했다.',
        keywords='대표자 개인사업자 종합소득세 상용근로자',
        agreement_cutoff='2026-10-23', computed=[['2025년 상용근로자 월평균 임금총액', OWNER_REFERENCE]]),
    rec('new-research-hire', '중소벤처기업부', '신진 연구인력 채용지원', '기업부설연구소·연구개발전담부서 보유 중소기업', ['hiring'],
        '1년차 기준연봉 학사 3,200 · 석사 4,100 · 박사 5,000만 원 · 그 40% 지원(장기근속 노력 시 50%) · 기업당 1명.',
        '기준연봉(1/2/3년차): 전문학사·학사 3,200/3,500/3,800만 원, 석사 4,100/4,500/4,900만 원, '
        '박사 5,000/5,500/6,000만 원. 기준연봉은 세전 기본급+월정액수당의 12개월 환산(퇴직금 제외). 기업당 1명, 최대 3년.',
        '지원액은 실제 연봉이 아니라 공고 기준연봉으로 산정한다. 50%는 협약일(2026-06-01) 후 1개월 안 내일채움공제 가입 '
        '또는 1년 내 중기부 계약학과 학위과정 지원 시(+10%p). 대상: 학·석·박사 학위 취득 후 5년 이내, 전문학사 7년 이내 '
        '(연구경력 2년 이상, 3년제 1년 이상, 연구전담요원 등록 경력 인정), 만 39세 이하, 정규직.',
        ['S13', 'S34'], evidence=['학위증명서', '정규직 근로계약서', '고용보험 가입 이력', '연구전담요원 등록'],
        note='고졸 단독 학력은 대상이 아니다. v1.0의 "최소 계약연봉"은 공고 용어가 아니며, 계약연봉을 기준연봉 이상으로 정해야 하는지는 '
             '공고 표 각주로 확인한다. 접수 마감 이후 인력 변경은 제한되며, 참여 6개월 이상이면 협약변경으로 1회 허용.',
        grades=DEGREE, keywords='신진 채용 연봉 기준연봉 최소 내일채움 계약학과 청년', minimum_contract=NEW_HIRE_MIN),
    rec('senior-research-hire', '중소벤처기업부', '고경력 연구인력 채용지원', '기업부설연구소·연구개발전담부서 보유 중소기업', ['hiring'],
        '세전 연봉의 50% · 1인당 연 5,000만 원 한도 · 최대 3년 · 기업당 1명.',
        '공고상 계약연봉 범위는 없다. 정부지원액은 적격 세전 연봉의 절반과 5,000만 원 중 낮은 금액이다.',
        '학위 취득 후 연구경력: 전문학사 16년, 학사 14년, 석사 10년, 박사 5년 이상. 제조AI 중소기업 예외에 해당하면 '
        '신진·고경력 각 1명 지원 가능.',
        ['S13', 'S36'], evidence=['학위증명서', '경력증명서(연구개발 경력)', '정규직 근로계약서'],
        note='5,000만 원 한도는 KOITA·정부24 안내에 있고 SMTECH 공고 페이지에는 "기준연봉의 50%"만 적혀 있다.',
        grades=DEGREE, keywords='고경력 경력 5000만', min_experience=SENIOR_EXPERIENCE),
    rec('public-dispatch', '중소벤처기업부', '공공연 연구인력 파견지원', '협약 요건을 충족한 중소기업과 공공연구기관', ['dispatch'],
        '파견 연구자 연봉의 50%(최대 3년) · 파견 인력을 기업 정규직으로 채용해 추가 연장하면 60%.',
        '개별 파견기관 연봉 기준이며 공고상 공통 원화 하한·상한은 없다. 기업당 1명.',
        '60%는 파견 인력을 기업 소속 정규직으로 채용한 경우에 한하며, 이때 해당 인력에게 별도 인센티브(정부 10%, 기업 5%)가 있다. '
        '파견기관 매칭과 승인이 필요하다. 11월 회차는 별도 공고를 확인한다.',
        ['S13', 'S35', 'S14'], evidence=['파견 협약서', '파견기관 연봉 확인', '정규직 전환 근로계약서'], keywords='파견 공공연 출연연'),
    rec('industrial-rd', '산업통상부', '산업기술혁신사업 R&D', '기업·대학·연구기관 협약 수행기관', ['employee', 'new'],
        '기관별 월·연 급여 × 계상률 · 참여연구자 최소 계상률 10%(학생 제외) · 현금은 별표 4·5 및 공고 예외.',
        '대학·기업은 월 급여, 출연연은 연 급여 기준. 학위별 정액은 없다. 위기지역 예외 상한은 정부지원연구개발비의 50%로 사업비에 연동된다.',
        '민군융합 제2026-374호 사례: 공고가 정한 일자 이후 신규 채용액 범위에서 기존 인력 현금 연동, 지식서비스·SW·설계기술(평가단 인정), '
        '창업 초기 7년, 전문연구사업자, 산업디자인전문회사, 육아 시간선택제 여성연구자(주 15~35시간), 산업위기지역 기업.',
        ['S16', 'S17', 'S18'], evidence=['계획서 표지 기술분류 코드', '평가 결과', '채용 증빙'],
        note='2026-09-01 행정예고된 개정안(S18)에 최소 인건비계상률 10% 규정 삭제가 들어 있다. 확정 고시 전까지는 현행 10%를 적용한다.',
        keywords='산업부 산자부 별표 위기지역 SW 계상률 10%'),
    rec('ict-rd', '과학기술정보통신부', 'ICT R&D(K-클라우드 공고 사례)', '중소·중견기업 등 제2026-0444호 수행기관', ['employee', 'new'],
        '신규 현금이 연차별 인건비 총액의 30% 이상이면 같은 금액까지 기존 인력 현금 · 미달 시 전액 불인정.',
        '실제 급여 기준. 학위별 정액 없음. 기존 인력 연동 현금의 최대액은 조건을 충족한 신규 인력의 해당 연도 현금 인건비다. '
        '신규 인력은 사업공고일 기준 6개월 이전부터 채용한 인력을 포함한다.',
        '정산 시 신규 현금이 30% 미만이면 해당 연도 기존 인력 현금 전액이 불인정된다. 30% 이상이어도 계획보다 신규 현금이 적으면 그 차액만큼 '
        '불인정. 청년 의무채용 5억 원당 1명, 고용유지 1년, 계상률 100% 등 별도 조건.',
        ['S19', 'S04'], evidence=['연차별 인건비 총액표(현금+현물)', '신규 인력 채용 증빙'], keywords='IITP ICT 30% 연동 클라우드'),
    rec('startup', '중소벤처기업부', '예비창업패키지', '창업진흥원·주관기관 사업화', ['employee', 'new'],
        '채용 예정 직원의 근로계약상 급여 · 학위별 금액표 없음 · 신청자 배우자·직계존비속 제외.',
        '사업에 직접 참여할 채용 예정 직원의 근로계약상 급여를 편성한다. 공고에 학위별 하한·상한은 없다.',
        '신청자의 배우자·직계존비속에게는 인건비를 지급할 수 없다. 총사업비는 정부지원사업비 100%.',
        ['S21', 'S20'], evidence=['근로계약서', '4대보험 가입 이력'],
        note='원공고 후 수정공고(제2026-143호, 제2026-207호)가 있으므로 최종 수정본을 기준으로 한다.', keywords='창업 예창패 사업화'),
    rec('content', '문화체육관광부', '지역 대표 글로컬 콘텐츠 제작·재투자', '한국콘텐츠진흥원 해당 사업', ['employee', 'owner'],
        '협약기간 중 제작·해외유통 참여 인력 급여 · 대표자는 자부담으로만.',
        '협약기간 내 제작·해외유통에 직접 참여한 인력의 급여를 인정한다. 학위별 급여 범위는 없다.',
        '대표자는 직접 참여한 경우에만 자부담금으로 편성할 수 있다. 협약 전 지출은 총사업비로 산정할 수 없다.',
        ['S22'], evidence=['참여 인력 업무일지', '급여 지급 증빙'], keywords='콘텐츠 콘진원 대표자'),
    rec('jb', '전북특별자치도', '혁신성장 R&D+ 1차(전북TP)', '전북테크노파크 공고 제2026-0048호', ['employee', 'new', 'student'],
        '신규 인력 현금 최대 2,470만 원 · 기존 인력 현금은 신규 인력 인건비의 50% 이내 · 신규+기존 합계 2,470만 원 이내.',
        '공고 [참고2] 사업비 편성기준(13쪽): 신규인력 현금인건비 최대 24.7백만 원, 기존인력 현금 한도는 신규인력 인건비의 50%, '
        '신규+기존 현금인건비 합계는 24.7백만 원을 넘을 수 없다. 대학·출연연 현금과 학생인건비는 도지원금 기준 한도를 따른다.',
        '신규인력은 공고가 정한 기준일 이후 채용자이며 재입사자는 제외. 지원금 0.9억 원당 1명 기준, 과제당 1명 신규채용 계획 제출 의무. '
        '지방보조사업이면 행안부 지방보조금 관리기준과 교부조건도 확인.',
        ['S24', 'S25'], note='v1.0은 "기존 인력 한도 문구와 산정 예시가 다르다"고 기록했다. 편성 전 공고 13쪽 산정 예시와 대조한다.',
        keywords='전북 테크노파크 지자체 2470 50%'),
    rec('gb', '경상북도', '미래차 부품 기술융합(경북TP)', '경북테크노파크 해당 사업', ['employee', 'new'],
        '기존 인력은 현물, 신규 인력만 현금(v1.0 기록, 공고문 미대조).',
        '과제 급여 기준. 학위별 금액표는 없고 승인된 세부 사업비를 따른다.',
        '기존 인력은 현물로, 신규 인력에 한해 현금으로 계상한다. 지방보조금 관리기준과 교부조건을 함께 확인한다.',
        ['S23', 'S25'], status='확인 필요',
        note='공고는 기업마당에 있으나(2026-02-26 게시, 신청 03-03~03-13) 인건비 조건은 첨부 공고문(hwp)에 있어 이번 검토에서 대조하지 못했다.',
        keywords='경북 테크노파크 지자체 미래차'),
    rec('youth-seoul', '고용노동부', '청년일자리도약장려금 · 수도권', '수도권 우선지원대상기업', ['hiring'],
        '기업지원 월 최대 60만 원 · 1년 720만 원 · 정규직 6개월 고용유지 · 월평균 급여 450만 원 이하.',
        '채용 근로조건: 최저임금 이상, 주 28시간 이상, 월평균 급여 450만 원 이하 등. 기업지원은 월 최대 60만 원, 1년 최대 720만 원.',
        '수도권은 취업애로청년(4개월 이상 실업, 채용일 기준 고졸 이하 등)만 대상이다. 대학 재학·휴학 중이면 고졸 요건을 적용하지 않는다. '
        '같은 신규 인력이 중앙부처·지자체 인건비 지원을 받으면 원칙적으로 제외(타 지원이 월 60만 원 미만이면 차액 규정 확인).',
        ['S26', 'S27'], evidence=['근로계약서', '고용보험 가입', '학력·취업애로 요건 증빙'],
        note='채용 전 참여 신청이 원칙이며, 이미 채용했다면 3개월 이내 신청 예외를 확인한다.',
        keywords='도약장려금 청년 고졸 취업애로 수도권', youth_cap=YOUTH['wage_cap']),
    rec('youth-local', '고용노동부', '청년일자리도약장려금 · 비수도권', '비수도권 5인 이상 우선지원대상기업·중견기업', ['hiring'],
        '기업지원 월 최대 60만 원 · 1년 720만 원 · 만 15~34세면 취업애로 요건 없음 · 청년 근속인센티브 별도.',
        '채용 근로조건은 수도권과 같다(주 28시간 이상, 월평균 급여 450만 원 이하 등). 청년 본인에게 2년간 지역별 480만·600만·720만 원 '
        '근속인센티브가 별도로 있다.',
        '고졸 여부와 관계없이 만 15~34세 청년이면 된다(취업애로 요건 없음). 타 정부 신규 인력 인건비 지원과 중복 시 원칙 제외.',
        ['S26', 'S27'], keywords='도약장려금 청년 비수도권 지방', youth_cap=YOUTH['wage_cap']),
    rec('koita-qualification', '과학기술정보통신부', '기업부설연구소 연구전담요원 자격', '기업부설연구소·연구개발전담부서', ['qualified'],
        '모든 기업: 자연계 학사 이상·기사 이상 · 중소기업 추가: 마이스터고·특성화고+경력 4년, 산업기사+2년, 기능사+4년, 자연계 전문학사+2년.',
        '연구전담요원 등록 자격 기준이다(시행규칙 제2조제4항). 임금 하한·상한이나 지원금 규정이 아니다. '
        '자연계 학사 이상과 기사 이상 자격은 기업 규모와 관계없이 인정된다.',
        '중소기업은 마이스터고·해당 특성화고 졸업+연구개발 경력 4년(졸업 전 경력 포함), 산업기사+2년, 기능사+4년, '
        '자연계 전문학사+2년(3년제 1년) 경로가 추가된다. 고졸은 기사 이상 자격이면 기업 규모와 관계없이 등록할 수 있다.',
        ['S15'], evidence=['학력·자격증 사본', '경력증명서'], keywords='연구전담요원 연구소 고졸 마이스터고 기사'),
    rec('central-contract', '재정경제부', '국가 발주 학술연구용역 단가', '국가기관 발주 계약', ['contract'],
        '월 22일·참여율 50%: 책임연구원 3,783,728원 · 연구원 2,901,312원 · 연구보조원 1,939,429원 · 보조원 1,454,621원.',
        '인건비 = 월 50% 단가 × (실제 참여율 ÷ 50%) × 참여 개월. 100% 환산은 2배(책임연구원 7,567,456원). '
        '2025년 단가(책임연구원 3,705,904원 등)에 2025년 소비자물가상승률 2.1%를 반영했다.',
        '예정가격 작성 기준단가다. 직급은 학위만으로 정하지 않고 발주처 제안요청서의 역할·자격 기준을 따른다. R&D 인건비 규정과 별개.',
        ['S28', 'S29', 'S31'], evidence=['제안요청서 직급 자격', '참여율 산출'],
        note='상여금·퇴직급여충당금은 발주 서식과 계약예규 허용 범위에서 별도 확인.',
        keywords='용역 학술 단가 책임연구원 예정가격', contract_rates=CONTRACT_RATE),
    rec('municipal-contract', '행정안전부', '지자체 발주 학술연구용역 단가', '지방자치단체 발주 계약', ['contract'],
        '국가 발주와 같은 2026년 단가(월 22일·참여율 50%) · 행안부 예규 제2장 별표 2.',
        '책임연구원 3,783,728원, 연구원 2,901,312원, 연구보조원 1,939,429원, 보조원 1,454,621원(월 22일·참여율 50%).',
        '행정안전부 예규의 예정가격 기준단가다. 발주처 직급·업무·자격 기준을 대조한다.',
        ['S30', 'S32'], keywords='지자체 용역 학술 단가', contract_rates=CONTRACT_RATE),
]

KEY_FIGURES = [
    dict(title='2026 최저임금', value='월 2,156,880원', sub='시간 10,320원 · 209시간', record='minimum-wage', refs=['S01']),
    dict(title='학생인건비 월 하한', value='130 · 220 · 300만 원', sub='학사 · 석사 · 박사 과정', record='student', refs=['S04']),
    dict(title='계상률 상한', value='월 100% · 연 130%', sub='영리·대학 · 출연연', record='national-company', refs=['S04']),
    dict(title='신진 채용 1년차 기준연봉', value='3,200 · 4,100 · 5,000만', sub='학사 · 석사 · 박사, 지원 40~50%', record='new-research-hire', refs=['S13']),
    dict(title='고경력 채용지원', value='연봉 50% · 연 5,000만', sub='최대 3년 · 기업당 1명', record='senior-research-hire', refs=['S13', 'S36']),
    dict(title='용역 연구원 월 단가', value='2,901,312원', sub='22일·참여율 50% 기준', record='central-contract', refs=['S28']),
    dict(title='도약장려금', value='월 60만 · 연 720만', sub='급여 450만 원 이하 채용', record='youth-seoul', refs=['S26']),
    dict(title='ICT 기존 인력 현금', value='신규 현금 30% 이상', sub='미달 시 연동분 전액 불인정', record='ict-rd', refs=['S19']),
]

GRADE_MATRIX = {
    'columns': ['고졸', '전문학사', '학사', '석사', '박사'],
    'rows': [
        {'label': '최저임금 월 환산', 'unit': '원, 2026년 209시간', 'refs': ['S01'], 'cells': ['2,156,880'] * 5},
        {'label': '국가 R&D 직원', 'unit': '기관별 산정 기준', 'refs': ['S04'], 'cells': ['실제 급여'] * 5},
        {'label': '국가 R&D 학생 계상기준 하한', 'unit': '만 원/월, 재학 과정 기준', 'refs': ['S04'],
         'cells': ['해당 없음', '130 이상', '130 이상', '220 이상', '300 이상']},
        {'label': '중기부 신진 기준연봉', 'unit': '만 원/년, 1/2/3년차', 'refs': ['S13'],
         'cells': ['대상 아님', '3,200 / 3,500 / 3,800', '3,200 / 3,500 / 3,800', '4,100 / 4,500 / 4,900', '5,000 / 5,500 / 6,000']},
        {'label': '중기부 신진 기본 지원(40%)', 'unit': '만 원/년, 1/2/3년차', 'refs': ['S13'],
         'cells': ['대상 아님', '1,280 / 1,400 / 1,520', '1,280 / 1,400 / 1,520', '1,640 / 1,800 / 1,960', '2,000 / 2,200 / 2,400']},
        {'label': '중기부 신진 요건 충족 시(50%)', 'unit': '만 원/년, 1/2/3년차', 'refs': ['S13'],
         'cells': ['대상 아님', '1,600 / 1,750 / 1,900', '1,600 / 1,750 / 1,900', '2,050 / 2,250 / 2,450', '2,500 / 2,750 / 3,000']},
        {'label': '중기부 고경력 경력 요건·지원 상한', 'unit': '학위 후 경력, 만 원/년', 'refs': ['S13'],
         'cells': ['대상 아님', '16년 이상 · 최대 5,000', '14년 이상 · 최대 5,000', '10년 이상 · 최대 5,000', '5년 이상 · 최대 5,000']},
        {'label': '연구전담요원 등록 경로', 'unit': '자격 기준, (중)은 중소기업만', 'refs': ['S15'],
         'cells': ['기사 이상 · (중) 마이스터고·특성화고+4년, 산업기사+2년, 기능사+4년', '(중) 자연계 전문학사+2년(3년제 1년)',
                   '자연계 학사 이상', '자연계 학사 이상', '자연계 학사 이상']},
    ],
    'notes': [
        '신진 채용 지원액은 실제 연봉이 아니라 공고 기준연봉으로 산정한다. 계약연봉을 기준연봉 이상으로 정해야 하는지는 공고 표 각주로 확인한다.',
        '최종학력이 고졸이어도 대학 과정에 재학하며 학생연구자 요건을 충족하면 재학 과정의 학생인건비 기준을 적용한다.',
        '학생 계상기준 하한은 기관이 정하는 기준의 최저선이며, 실제 지급액은 기관 기준·확약서·지급률에 따른다.',
    ],
}

GLOSSARY = [
    ['계상률', '해당 기간에 과제에 계상하는 인건비를 기준 급여로 나눈 비율.'],
    ['총인건비계상률', '한 사람이 참여한 모든 과제의 인건비·학생인건비·미지급인건비 계상률의 합. 영리·대학은 월 100% 이내.'],
    ['현금 / 현물', '현금은 정부지원금·기관부담 현금으로 실제 지급하는 인건비, 현물은 기관이 이미 부담하는 급여를 인정액으로 잡는 것.'],
    ['신규채용(현금 예외)', '국가 R&D 고시상 공고일 전 6개월 이내 채용자를 포함. 중기부 지침은 개발 종료일까지 채용자 포함.'],
    ['전문연구사업자', '법정 업종을 영위하고 신고한 연구개발서비스업자. 소속 참여연구자는 현금 계상 가능.'],
    ['연구근접지원인력', '연구 현장에서 연구를 직접 지원하는 인력. 대학·비영리는 직접비, 영리기관 연구지원인력은 간접비 기준.'],
    ['학생인건비 계상기준', '기관이 재학 과정별로 정하는 월 기준액. 고시 하한(학사 130·석사 220·박사 300만 원) 이상.'],
    ['통합관리기관', '학생인건비를 기관 단위로 통합 관리하도록 지정된 기관(S06 목록).'],
    ['기준연봉(신진 채용)', '공고가 학위·연차별로 정한 연봉. 정부지원액(40%·50%)은 이 금액으로 산정한다. 세전 기본급과 월정액수당의 12개월 환산, 퇴직금 제외.'],
    ['부처 명칭', '산업통상자원부는 2025-10-01 산업통상부로, 기획재정부는 2026-01-02 재정경제부·기획예산처로 개편됐다. 개편 전 고시는 발령 당시 명칭을 쓴다.'],
    ['예정가격 기준단가', '학술연구용역 발주 시 예정가격 작성에 쓰는 직급별 월 단가(22일·참여율 50%).'],
    ['월 209시간', '주 40시간 + 유급 주휴 8시간을 월 평균으로 환산한 시간. 최저임금 월 환산에 사용.'],
]

PENDING = [
    '2027-01-01부터 최저임금 시간급 10,700원(월 2,236,300원)을 적용한다(S37).',
    '과기정통부 연구개발비 사용 기준 개정안(S05)은 2027-01-01 시행 예정이다. 연구수당 1인 지급 상한(계상액의 70%, 본인 인건비의 100%)이 '
    '새로 생긴다. 학생인건비 하한과 계상률은 바뀌지 않는다. 최종 고시 전까지 반영하지 않았다.',
    '산업통상부 공통 운영요령 개정안(S18, 2026-09-01 행정예고)에 최소 인건비계상률 10% 삭제가 들어 있다. 확정 고시 여부를 확인한다.',
    '중기부 관리지침(S09)의 부칙·개인사업자 대표 기준 문구는 대학 산학협력단 재게시본으로만 확인했다. IRIS 자료실 원문과 대조가 필요하다.',
    '공정최적화 R&D(S11)의 청년 의무채용 조건과 경북TP(S23)의 인건비 조건은 첨부 공고문(hwp)과 대조하지 못했다.',
    '신진 연구인력 채용지원의 계약연봉이 기준연봉 이상이어야 하는지는 공고 표 각주로 확인이 필요하다.',
]

CHANGES = [
    ['2026-11-17 v2.0', '키워드 검색, 한 줄 요약·펼침 구조, 핵심 수치 카드, 학력별 비교표, 계산기 6종, 출처 번호(S01~S37)를 추가했다. '
                        '학력 선택이 실제로 결과를 거르도록 고쳤다. 깨진 출처 링크를 교체했다. 사실관계 검토 결과를 반영했다'
                        '(신진 "기준연봉" 용어, 기업당 1명, 파견 60% 조건, 연구전담요원 경로, 전북TP 기존 인력 50% 한도, 개정 예고).'],
    ['2026-11-17 v1.0', '최초 공개(21개 기준).'],
]


def evaluate(item, *, grade='', course='', year=1, salary=None, agreement_date='', contract_rank=''):
    """웹 페이지 evaluate()와 같은 규칙으로 상태와 계산값을 돌려준다."""
    status, amounts = None, []
    if agreement_date and item.get('agreement_cutoff', '') > agreement_date:
        return f'협약일이 {item["agreement_cutoff"]} 이전 · 협약 당시 지침 적용', amounts
    if grade and item['grades'] and grade not in item['grades']:
        return '학력 요건 미해당', amounts
    if 'minimum_contract' in item and grade:
        minimum = item['minimum_contract'][grade][year - 1] * 10_000
        amounts = [['연차별 기준연봉', minimum], ['기본 정부지원(40%)', minimum * 4 // 10],
                   ['요건 충족 시 정부지원(50%)', minimum // 2]]
        if salary is not None:
            status = '입력 연봉이 기준연봉 이상' if salary * 12 >= minimum else '입력 연봉이 기준연봉 미만 · 공고 확인'
    elif 'min_experience' in item and grade:
        status = f'학위 취득 후 연구경력 {item["min_experience"][grade]}년 이상 필요'
        if salary is not None:
            amounts = [['입력 급여 기준 연간 지원 상한', min(salary * 6, SENIOR_CAP)]]
    elif 'student_floor' in item and course:
        amounts = [['과정별 기관 계상기준 하한(월)', item['student_floor'][course]]]
    elif 'contract_rates' in item and contract_rank:
        amounts = [['월 기준단가(22일·참여율 50%)', item['contract_rates'][contract_rank]]]
    elif 'youth_cap' in item and salary is not None:
        status = '월평균 급여 조건 이내' if salary <= item['youth_cap'] else '월평균 급여 한도 초과'
    elif item['id'] == 'minimum-wage' and salary is not None:
        status = '월 환산 최저임금 이상' if salary >= MIN_WAGE_MONTH else '월 환산 최저임금 미달(209시간 기준)'
    amounts += item.get('computed', [])
    return status, amounts


def _norm(text):
    return re.sub(r'[,\s·]', '', str(text).lower())


def lookup(*, agency='', program='', grade='', role='', course='', year=1, salary=None,
           agreement_date='', contract_rank='', search='', include_ineligible=False):
    terms = [_norm(t) for t in search.split() if _norm(t)]
    results = []
    for item in RULES:
        if agency and agency != item['agency'] or program and program != item['id']:
            continue
        if role and role not in item['roles']:
            continue
        if terms:
            hay = _norm(' '.join([item['agency'], item['name'], item['organization'], item['summary'], item['amount'],
                                  item['cash'], ' '.join(item['evidence']), item['note'], item['keywords']]
                                 + [SOURCES[r]['title'] + SOURCES[r]['docNo'] for r in item['refs']]))
            if not all(t in hay for t in terms):
                continue
        if grade and item['grades'] and grade not in item['grades'] and not include_ineligible:
            continue
        status, amounts = evaluate(item, grade=grade, course=course, year=year, salary=salary,
                                   agreement_date=agreement_date, contract_rank=contract_rank)
        results.append({**item, 'check': status, 'computed_krw': amounts,
                        'sources': [{'id': r, **SOURCES[r]} for r in item['refs']]})
    return results


def validate():
    """데이터 내부 일관성 검사. build_html.py가 빌드 전에 호출한다."""
    errors = []
    for item in RULES:
        for ref in item['refs']:
            if ref not in SOURCES:
                errors.append(f'{item["id"]}: 없는 출처 {ref}')
    used = {ref for item in RULES for ref in item['refs']} | {r for k in KEY_FIGURES for r in k['refs']}
    used |= {r for row in GRADE_MATRIX['rows'] for r in row['refs']}
    for sid in SOURCES:
        if sid not in used and sid not in DOC_ONLY_SOURCES:
            errors.append(f'출처 {sid}가 어떤 기준에도 연결되지 않음')
    ids = [r['id'] for r in RULES]
    if len(ids) != len(set(ids)):
        errors.append('중복 id')
    for k in KEY_FIGURES:
        if k['record'] not in ids:
            errors.append(f'핵심 수치 카드의 연결 대상 없음: {k["record"]}')
    # 숫자 교차 검증
    if MIN_WAGE['2026'] * 209 != 2_156_880 or MIN_WAGE['2027'] * 209 != 2_236_300:
        errors.append('최저임금 월 환산 불일치')
    for grade, values in NEW_HIRE_MIN.items():
        row40 = GRADE_MATRIX['rows'][4]['cells'][GRADE_MATRIX['columns'].index(GRADES[grade])]
        row50 = GRADE_MATRIX['rows'][5]['cells'][GRADE_MATRIX['columns'].index(GRADES[grade])]
        if row40 != ' / '.join(f'{v * 4 // 10:,}' for v in values) or row50 != ' / '.join(f'{v // 2:,}' for v in values):
            errors.append(f'신진 지원액 표 불일치: {grade}')
    for rank, rate in CONTRACT_RATE.items():
        if f'{rate:,}원' not in RULES[ids.index('central-contract')]['summary']:
            errors.append(f'용역 단가 요약 불일치: {rank}')
    return errors


def main():
    parser = argparse.ArgumentParser(description=f'{AS_OF} 정부지원사업 인건비 기준 조회 (데이터 v{VERSION})')
    parser.add_argument('search', nargs='*', help='키워드 검색. 예: 학생 현금')
    parser.add_argument('--agency', choices=sorted({r['agency'] for r in RULES}), default='')
    parser.add_argument('--program', choices=[r['id'] for r in RULES], default='')
    parser.add_argument('--grade', choices=GRADES, default='', help='최종학력. hs/associate/bachelor/master/doctor')
    parser.add_argument('--role', choices=ROLES, default='')
    parser.add_argument('--course', choices=COURSES, default='', help='현재 재학 중인 학생연구자 과정')
    parser.add_argument('--year', type=int, choices=(1, 2, 3), default=1)
    parser.add_argument('--salary', type=int, help='월 세전 원화')
    parser.add_argument('--agreement-date', default='', help='해당 과제 협약일 YYYY-MM-DD')
    parser.add_argument('--contract-rank', choices=CONTRACT_RATE, default='')
    parser.add_argument('--brief', action='store_true', help='한 줄 요약만 출력')
    parser.add_argument('--json', action='store_true')
    parser.add_argument('--check', action='store_true', help='데이터 일관성 검사만 실행')
    args = parser.parse_args()
    if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
        sys.stdout.reconfigure(encoding='utf-8')
    if args.check:
        errors = validate()
        print('\n'.join(errors) or f'일관성 검사 통과: 기준 {len(RULES)}개, 출처 {len(SOURCES)}개')
        sys.exit(1 if errors else 0)
    if args.salary is not None and args.salary < 0:
        parser.error('월 급여는 0원 이상이어야 합니다.')
    if args.agreement_date:
        from datetime import date
        try:
            args.agreement_date = date.fromisoformat(args.agreement_date).isoformat()
        except ValueError:
            parser.error('협약일을 YYYY-MM-DD로 입력하세요.')
    results = lookup(agency=args.agency, program=args.program, grade=args.grade, role=args.role, course=args.course,
                     year=args.year, salary=args.salary, agreement_date=args.agreement_date,
                     contract_rank=args.contract_rank, search=' '.join(args.search))
    if args.json:
        print(json.dumps({'checked_on': AS_OF, 'version': VERSION, 'results': results}, ensure_ascii=False, indent=2))
        return
    print(f'원문 확인일 {AS_OF} · {len(results)}개 기준')
    for r in results:
        check = f' · {r["check"]}' if r['check'] else ''
        print(f'\n[{r["agency"]}] {r["name"]}{check}\n  {r["summary"]}')
        for label, amount in r['computed_krw']:
            print(f'  {label} {amount:,}원')
        if args.brief:
            continue
        print(f'  금액·산정: {r["amount"]}\n  현금·자격: {r["cash"]}')
        if r['evidence']:
            print('  증빙: ' + ', '.join(r['evidence']))
        if r['note']:
            print(f'  주의: {r["note"]}')
        for s in r['sources']:
            print(f'  [{s["id"]}] {s["title"]} {s["docNo"]} · {s["date"]} · {s["section"]}\n       {s["url"]}')


if __name__ == '__main__':
    main()

# 정부지원사업 인건비 기준 조회

공개 법령·고시·사업공고를 바탕으로 2026년 11월 17일 기준의 적용 근거를 조회합니다. 기관·사업·최종학력과 인력 유형을 선택하고, 필요한 경우 급여·연차·협약일을 입력합니다.

## HTML

`index.html`을 브라우저에서 직접 엽니다. GitHub Pages를 사용할 때는 기본 브랜치 루트의 `index.html`을 게시합니다. 입력값은 브라우저 안에서 처리됩니다.

`page.html`은 생성용 템플릿입니다. `wage_rules.py`나 템플릿을 바꾼 뒤 `python build_html.py`로 `index.html`을 다시 생성합니다.

## Python 조회

Python 3.10 이상에서 별도 패키지 없이 실행됩니다.

```powershell
python wage_rules.py --help
python wage_rules.py --program new-research-hire --grade hs
python wage_rules.py --program new-research-hire --grade master --year 2 --salary 3800000
python wage_rules.py --program mss-rd --role employee --agreement-date 2026-10-22
python wage_rules.py --program student --grade hs --course bachelor --json
python wage_rules.py --program municipal-contract --contract-rank 연구원
```

`--salary`는 월 세전 원화입니다. 프로그램마다 산입 임금의 범위가 다릅니다. `--grade`는 취득한 최종학력이고 `--course`는 현재 재학 과정입니다. `--agreement-date`는 중기부 기술개발 관리지침의 적용 시점 확인에 사용합니다.

표시된 숫자는 임금 하한, 계약연봉 요건, 예정가격 기준단가 또는 지원금 상한 중 표시된 항목에 해당합니다. 개인·사업장·과제의 적격 여부와 실제 인정액은 공고·협약·증빙으로 확인합니다.

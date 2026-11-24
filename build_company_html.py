"""공개 회사 과제 조회 화면이나 사내용 프로필로 채운 HTML을 생성한다."""

import argparse
import json
from pathlib import Path

from company_wage_rules import CITIES, GRADES, INDUSTRIES, PORTFOLIO_AS_OF, ROLES, RULES, SOURCES


def main():
    base = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', type=Path)
    parser.add_argument('--output', type=Path, default=base / 'company.html')
    args = parser.parse_args()
    roles = {key: text for key, text in ROLES.items() if any(key in row['roles'] for row in RULES)}
    model = {'portfolioAsOf': PORTFOLIO_AS_OF, 'cities': CITIES, 'industries': INDUSTRIES,
             'grades': GRADES, 'roles': roles, 'records': RULES, 'sources': SOURCES}
    template = (base / 'company_template.html').read_text(encoding='utf-8')
    if args.profile:
        if args.output.resolve().is_relative_to(base):
            parser.error('회사 프로필을 포함한 HTML은 GitHub 게시용 폴더 밖에 저장하세요.')
        profile = json.loads(args.profile.read_text(encoding='utf-8-sig'))
        evidence = profile.pop('projectEvidence', {})
        unknown = evidence.keys() - {row['id'] for row in RULES if row.get('portfolio')}
        if unknown:
            parser.error(f'회사 근거에 등록되지 않은 과제 ID가 있습니다. {", ".join(sorted(unknown))}')
        model['profile'] = profile
        model['companyEvidence'] = evidence
        template = template.replace('href="./index.html"',
                                    'href="https://kimweejun.github.io/government-wage-standards/"')
    payload = json.dumps(model, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c')
    assert template.count('/*__DATA__*/') == 1
    args.output.write_text(template.replace('/*__DATA__*/', payload), encoding='utf-8')


if __name__ == '__main__':
    main()

"""Deterministic demo engine. No LLM or invented facts."""
import re
from .models import uid

SKILLS = {
    '문제 해결': ['문제', '해결', '오류', 'fix', 'bug', 'error', 'timeout', '개선'],
    '협업': ['협업', '팀', '공동', 'review', '협력'],
    '의사소통': ['소통', '회의', '설명', '문서', 'docs', '발표'],
    '리더십': ['리더', '주도', '이끌', '팀장'],
    '책임감': ['책임', '마감', '완수'],
    '도전': ['도전', '새로운', '처음'],
    '분석력': ['분석', '로그', '데이터', '원인'],
    '기술 활용': ['api', '개발', '코드', '기술', '구현', '테스트'],
    '프로젝트 관리': ['일정', '관리', '계획', '우선순위'],
}

def skills_for(text):
    return [name for name, words in SKILLS.items() if any(w in text.lower() for w in words)]

def organize_note(text):
    fields = dict(situation='', task='', action='', result='')
    labels = {'상황':'situation','배경':'situation','과제':'task','역할':'task',
              '행동':'action','수행':'action','결과':'result','성과':'result'}
    unmatched = []
    for line in text.splitlines():
        key, sep, value = line.partition(':')
        target = labels.get(key.strip())
        if sep and target:
            fields[target] += (' ' if fields[target] else '') + value.strip()
        elif line.strip():
            unmatched.append(line.strip())
    if unmatched:
        fields['situation'] = '\n'.join(filter(None, [fields['situation'], *unmatched]))
    questions = [f'{label}에 대해 실제로 확인한 내용을 적어 주세요.'
                 for key, label in [('task','맡은 역할'),('action','본인이 수행한 행동'),('result','결과')]
                 if not fields[key]][:2]
    return dict(**fields, skills=skills_for(text), questions=questions, mode='demo',
                notice='규칙 기반 데모: 상황/역할/행동/결과 라벨을 분리합니다. 라벨 없는 메모는 상황에 보존합니다.')

def candidates_for(source):
    return [dict(id=uid(), title=item['excerpt'].split('\n')[0][:160],
            skills=skills_for(item['excerpt']), evidence=[item], verification_status='needs_confirmation',
            questions=['이 활동에서 본인이 실제 수행한 행동은 무엇인가요?', '작업 후 직접 확인한 결과가 있나요?'])
            for item in source['activities'][:12]]

def analyze_question(question, description):
    return dict(required_skills=skills_for(question + ' ' + description),
                required_elements=['문제 상황', '본인 역할', '구체적 행동', '확인한 결과'],
                mode='demo', notice='키워드 기반 데모 분석입니다. 의미 분석이나 채용 적합도 평가가 아닙니다.')

def match_experiences(application, experiences):
    desired = set(application.analysis['required_skills'])
    query_words = set(re.findall(r'[\w가-힣]{2,}', application.question.lower()))
    ranked = []
    for exp in experiences:
        text = ' '.join([exp.title, exp.situation, exp.task, exp.action, exp.result])
        related = sorted(desired.intersection(exp.skills))
        overlap = query_words.intersection(re.findall(r'[\w가-힣]{2,}', text.lower()))
        if not related and not overlap:
            continue
        missing = [label for key, label in [('situation','상황'),('task','역할'),('action','본인 행동'),('result','결과')]
                   if not getattr(exp, key)]
        if exp.verification_status != 'user_confirmed':
            missing.append('본인 활동·사실 확인')
        ranked.append(dict(experience_id=exp.id, title=exp.title, related_skills=related,
            relevance_score=len(related)*10+len(overlap),
            reason=f"문항과 {', '.join(related) or ', '.join(sorted(overlap))} 키워드가 연결됩니다.",
            missing_information=missing, action=exp.action, result=exp.result,
            is_sample=exp.is_sample, verification_status=exp.verification_status, evidence_count=len(exp.evidence)))
    return sorted(ranked, key=lambda x: x['relevance_score'], reverse=True)[:3]

def build_draft(exp, limit):
    statements = []
    warnings = ['규칙 기반 데모: 확인한 경험의 문장을 그대로 조합했습니다. 문항·기업·직무에 맞는 표현은 직접 다듬어 주세요.']
    for key, label in [('situation','상황'),('task','역할'),('action','행동'),('result','결과'),('lessons','배운 점')]:
        value = getattr(exp, key).strip()
        if not value:
            if key != 'lessons':
                warnings.append(f'{label}: 확인 필요')
            continue
        for sentence in re.split(r'(?<=[.!?])\s+|\n+', value):
            if sentence and sentence not in statements:
                candidate = ' '.join(statements + [sentence])
                if limit is None or len(candidate) <= limit:
                    statements.append(sentence)
                else:
                    warnings.append('글자 수 제한으로 일부 문장을 제외했습니다. 내용의 완결성을 확인해 주세요.')
    return ' '.join(statements), statements, list(dict.fromkeys(warnings))

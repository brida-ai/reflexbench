"""Canonical Reflex/System One request contract v1.

Reflex v1 does not optimize prompts per engine. It validates a provider-neutral request:
`state + typed questions`. The only wire normalization is the product-friendly `binary`
alias to the System One `noul` primitive. Model-specific prompting/config belongs outside
this contract and cannot be used to claim Reflex harness uplift.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

QUESTION_KEYS = frozenset({'type','instructions','criteria'})
RECIPE_ENGINE_KEYS = frozenset({'model','engine','provider','adapter','temperature','prompt','systemPrompt'})
QUESTION_ENGINE_KEYS = frozenset({'model','engine','provider','adapter','temperature','prompt','systemPrompt'})


def _nonempty_text(value: Any, field: str) -> str:
    if not isinstance(value,str) or not value.strip():
        raise ValueError(f'{field} must be a non-empty string')
    return value


def _criteria_mapping(value: Any, *, minimum: int) -> dict[str,str]:
    if not isinstance(value,Mapping):
        raise ValueError('choice criteria must be a mapping')
    out: dict[str,str]={}
    for raw_label, raw_text in value.items():
        label=_nonempty_text(str(raw_label), 'choice criterion label')
        text=_nonempty_text(raw_text, f'choice criterion {label!r}')
        if label in out:
            raise ValueError('choice criterion labels must be unique')
        out[label]=text
    if len(out)<minimum:
        raise ValueError(f'choice criteria must contain at least two options')
    return out


def _score_criteria(value: Any) -> list[str]:
    if not isinstance(value,Sequence) or isinstance(value,(str,bytes,bytearray)):
        raise ValueError('score criteria must be an ordered list')
    out=[_nonempty_text(item,'score criterion') for item in value]
    if len(out)<2:
        raise ValueError('score criteria must contain at least two ordered levels')
    return out


def normalize_question(question: Mapping[str,Any]) -> dict[str,Any]:
    if not isinstance(question,Mapping):
        raise ValueError('question must be an object')
    extra=set(question)-QUESTION_KEYS
    if extra:
        raise ValueError(f'unsupported question keys: {sorted(extra)!r}')
    if set(question)&QUESTION_ENGINE_KEYS:
        raise ValueError('engine-specific question configuration is forbidden')

    raw_type=str(question.get('type','')).strip().lower()
    if raw_type not in {'binary','noul','choice','score'}:
        raise ValueError(f'unsupported System One question type: {raw_type!r}')
    instructions=_nonempty_text(question.get('instructions'),'question instructions')
    wire_type='noul' if raw_type=='binary' else raw_type
    out: dict[str,Any]={'type':wire_type,'instructions':instructions}

    if raw_type in {'binary','noul'}:
        criteria=question.get('criteria')
        if criteria is not None:
            if not isinstance(criteria,Mapping):
                raise ValueError('binary/noul criteria must be a mapping when supplied')
            normalized={str(k):_nonempty_text(v,f'binary criterion {k!r}') for k,v in criteria.items()}
            if set(normalized)!={'true','false'}:
                raise ValueError("binary/noul criteria keys must be exactly 'true' and 'false'")
            out['criteria']=normalized
    elif raw_type=='choice':
        out['criteria']=_criteria_mapping(question.get('criteria'),minimum=2)
    else:
        out['criteria']=_score_criteria(question.get('criteria'))
    return out


def normalize_questions(questions: Mapping[str,Mapping[str,Any]]) -> dict[str,dict[str,Any]]:
    if not isinstance(questions,Mapping) or not questions:
        raise ValueError('questions must be a non-empty mapping')
    out: dict[str,dict[str,Any]]={}
    for raw_id, question in questions.items():
        qid=_nonempty_text(str(raw_id),'question id')
        if qid in out:
            raise ValueError('question ids must be unique')
        out[qid]=normalize_question(question)
    return out


def compile_request(state: Any, questions: Mapping[str,Mapping[str,Any]]) -> dict[str,Any]:
    """Compile one provider-neutral System One request without rewriting state semantics."""
    return {'state':state,'questions':normalize_questions(questions)}


def _recipe_question_type(question: Mapping[str,Any]) -> str:
    raw=str(question.get('type','')).strip().lower()
    return 'binary' if raw=='noul' else raw


def validate_recipe(recipe: Mapping[str,Any]) -> None:
    if not isinstance(recipe,Mapping):
        raise ValueError('recipe must be an object')
    forbidden=sorted(set(recipe)&RECIPE_ENGINE_KEYS)
    if forbidden:
        raise ValueError(f'recipe contains engine-specific configuration: {forbidden!r}')
    questions=recipe.get('questions')
    normalize_questions(questions)  # validates the provider-neutral engine payload
    policy=recipe.get('declarative_policy')
    if not isinstance(policy,Mapping):
        raise ValueError('recipe requires declarative_policy')
    qid=policy.get('questionId')
    if not isinstance(qid,str) or qid not in questions:
        raise ValueError('declarative_policy.questionId must reference an existing question')
    policy_type=str(policy.get('type','')).strip().lower()
    qtype=_recipe_question_type(questions[qid])
    if policy_type!=qtype:
        raise ValueError(f'declarative policy type {policy_type!r} does not match question type {qtype!r}')


def compile_recipe_request(recipe: Mapping[str,Any], state: Any) -> dict[str,Any]:
    validate_recipe(recipe)
    return compile_request(state,recipe['questions'])

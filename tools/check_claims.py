#!/usr/bin/env python3
from __future__ import annotations
import json
import sys
from pathlib import Path

root=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve()
results=root/'results'/'v1'
readme=(root/'README.md').read_text()
report=(root/'RESULTS.md').read_text()

def load(name): return json.loads((results/name).read_text())
def pct(v): return f'{100*float(v):.1f}%'
def pp(v): return f'{100*float(v):+.1f} pp'
def f3(v): return f'{float(v):.3f}'
def ms1(v): return f'{float(v):.1f} ms'
def require(text, needle, label):
    if needle not in text:
        raise SystemExit(f'claim mismatch [{label}]: expected {needle!r}')

core=load('reflex-core-v1-typesafe-jev-public110.json')
g1=load('reflex-core-v1-workflow-gate-evaluation.json')
g2=load('reflex-core-v1-workflow-gate-v2-evaluation.json')
cr=core['raw']; cc=core['reflex_core_v1']; o1=g1['overall']; o2=g2['overall']
require(report, f"| Public product fixtures (Jev) | {pct(cr['semantic_accuracy'])} | **{pct(cc['operational_accuracy'])}** | {pp(cc['delta_vs_raw'])} | {cc['rescues']} / {cc['harms']} | {cr['n']}/{cr['n']} |", 'core-product110')
require(report, f"| Blind workflow Gate v1 (Jev) | {pct(o1['raw_exact_branch_accuracy'])} | **{pct(o1['core_exact_branch_accuracy'])}** | {pp(o1['paired_delta'])} | {o1['rescues']} / {o1['harms']} | {g1['completion']['completed']}/150 — **FAIL** |", 'core-gate-v1')
require(report, f"| Blind workflow Gate v2 (Jev) | {pct(o2['raw_exact_branch_accuracy'])} | **{pct(o2['core_exact_branch_accuracy'])}** | {pp(o2['paired_delta'])} | {o2['rescues']} / {o2['harms']} | {g2['completion']['completed']}/150 — **PASS** |", 'core-gate-v2')
require(readme, f"**Same-response Reflex Core proof:** TypeSafe Jev raw semantic accuracy **{pct(cr['semantic_accuracy'])} ({cr['semantic_correct']}/{cr['n']}) -> {pct(cc['operational_accuracy'])} ({cc['operational_correct']}/{cr['n']})**", 'readme-product110')
require(readme, f"**Independent blind workflow replication:** **{pct(o2['raw_exact_branch_accuracy'])} raw -> {pct(o2['core_exact_branch_accuracy'])} Core** on 150/150 completed cases; paired delta **{pp(o2['paired_delta'])}**", 'readme-gate-v2')

hard={
 'TypeSafe Jev': ('jevbench-public-hard-typesafe-jev-consolidated.json','hosted route','latency_ms_successful_responses'),
 'upstream Reflex / Qwen3.5-2B': ('jevbench-public-hard-qwen-reflex-2b-rtx3070.json','local RTX 3070 HTTP','latency_ms'),
 'jeff / GLiFormer ~400M': ('jevbench-public-hard-jeff-rtx3070.json','local RTX 3070 HTTP','latency_ms'),
 'openJev Verdict 1.4 / 151M': ('jevbench-public-hard-verdict-1.4-rtx3070.json','local RTX 3070 HTTP','latency_ms'),
 'Laya base / 421M': ('jevbench-public-hard-laya-base-http-rtx3070.json','local RTX 3070 HTTP','latency_ms'),
 'Kev-0.8B': ('jevbench-public-hard-kev-0.8b-rtx3070.json','local RTX 3070 HTTP','latency_ms'),
}
for display,(name,boundary,latkey) in hard.items():
    d=load(name); m=d['metrics']; lat=d[latkey]['p50']
    accuracy=pct(m['accuracy'])
    if display=='TypeSafe Jev': accuracy='**'+accuracy+'**'
    row=f"| {display} | {accuracy} | {f3(m['ece'])} | {f3(m['score_mae'])} | {ms1(lat)} | {boundary} |"
    require(report,row,'hard-'+display)

q=load('jevbench-public-hard-qwen35-08b-base-readout-rtx3070-reference-kernel.json')['metrics']
require(report,f"| frozen Qwen3.5-0.8B readout control | {pct(q['accuracy'])} | {f3(q['ece'])} | {f3(q['score_mae'])} | excluded | reference kernels |",'hard-qwen08-control')

massive=load('massive-en-es-comparison.json')['lanes']
for lane,title in [('massive-en-es-common20','common20'),('massive-en-es-high60','high60')]:
    jev=massive[lane]['engines']['typesafe-jev']; pair=jev['paired_language']
    require(report,pct(jev['accuracy']),f'{title}-jev-accuracy')
    require(report,pct(pair['en_accuracy']),f'{title}-jev-en')
    require(report,pct(pair['es_accuracy']),f'{title}-jev-es')
    require(report,pct(pair['prediction_consistency']),f'{title}-jev-consistency')

print('published claim verification: OK')

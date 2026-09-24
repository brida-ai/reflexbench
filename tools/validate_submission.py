#!/usr/bin/env python3
"""Validate the stable ReflexBench v1 result-submission envelope without third-party deps."""
from __future__ import annotations
import argparse, datetime as dt, json, re, sys
from pathlib import Path

SCHEMA = "reflexbench.result-submission/v1"
REQUIRED_TOP = {"schema","benchmark_version","lane","engine","adapter","corpus","deployment","run","metrics","evidence"}
HEX64 = re.compile(r"^[0-9a-f]{64}$")

def fail(errors:list[str], message:str) -> None: errors.append(message)
def is_nonempty(v:object) -> bool: return isinstance(v,str) and bool(v.strip())
def rate(errors:list[str], obj:dict, key:str, *, required:bool=False) -> None:
    if key not in obj:
        if required: fail(errors,f"metrics.{key} is required")
        return
    v=obj[key]
    if v is None and not required: return
    if not isinstance(v,(int,float)) or isinstance(v,bool) or not 0 <= float(v) <= 1:
        fail(errors,f"metrics.{key} must be a number in [0,1]")

def validate(d:object) -> list[str]:
    e:list[str]=[]
    if not isinstance(d,dict): return ["submission must be a JSON object"]
    missing=sorted(REQUIRED_TOP-set(d));
    if missing: fail(e,"missing top-level keys: "+", ".join(missing))
    if d.get("schema") != SCHEMA: fail(e,f"schema must be {SCHEMA!r}")
    if d.get("benchmark_version") != "1.0.0": fail(e,"benchmark_version must be '1.0.0'")
    if not is_nonempty(d.get("lane")): fail(e,"lane must be a non-empty string")
    for section, keys in {"engine":("owner","name","revision"),"adapter":("revision",),"corpus":("name","sha256","rows"),"deployment":("kind",),"run":("date","command","retry_policy")}.items():
        obj=d.get(section)
        if not isinstance(obj,dict): fail(e,f"{section} must be an object"); continue
        for k in keys:
            if k not in obj: fail(e,f"{section}.{k} is required")
    engine=d.get("engine",{}) if isinstance(d.get("engine"),dict) else {}
    for k in ("owner","name","revision"):
        if k in engine and not is_nonempty(engine[k]): fail(e,f"engine.{k} must be non-empty")
    corpus=d.get("corpus",{}) if isinstance(d.get("corpus"),dict) else {}
    if "sha256" in corpus and (not isinstance(corpus["sha256"],str) or not HEX64.fullmatch(corpus["sha256"])): fail(e,"corpus.sha256 must be 64 lowercase hex chars")
    if "rows" in corpus and (not isinstance(corpus["rows"],int) or isinstance(corpus["rows"],bool) or corpus["rows"] < 1): fail(e,"corpus.rows must be a positive integer")
    deployment=d.get("deployment",{}) if isinstance(d.get("deployment"),dict) else {}
    if deployment.get("kind") not in {"hosted-api","local-cpu","local-gpu","other"}: fail(e,"deployment.kind is invalid")
    run=d.get("run",{}) if isinstance(d.get("run"),dict) else {}
    if "date" in run:
        try: dt.date.fromisoformat(run["date"])
        except Exception: fail(e,"run.date must be YYYY-MM-DD")
    for k in ("command","retry_policy"):
        if k in run and not is_nonempty(run[k]): fail(e,f"run.{k} must be non-empty")
    metrics=d.get("metrics")
    if not isinstance(metrics,dict): fail(e,"metrics must be an object")
    else:
        rate(e,metrics,"completion_rate",required=True); rate(e,metrics,"semantic_accuracy",required=True); rate(e,metrics,"operational_accuracy");
        for k in ("ece","p50_latency_ms"):
            if k in metrics and metrics[k] is not None and (not isinstance(metrics[k],(int,float)) or isinstance(metrics[k],bool) or metrics[k] < 0): fail(e,f"metrics.{k} must be null or non-negative")
    evidence=d.get("evidence")
    if not isinstance(evidence,dict): fail(e,"evidence must be an object")
    else:
        paths=evidence.get("receipt_paths")
        if not isinstance(paths,list) or not paths or any(not is_nonempty(x) for x in paths): fail(e,"evidence.receipt_paths must be a non-empty list of paths")
        if not isinstance(evidence.get("benchmark_used_for_development"),bool): fail(e,"evidence.benchmark_used_for_development must be boolean")
    return e

def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument("submission",type=Path); args=ap.parse_args()
    try: data=json.loads(args.submission.read_text())
    except Exception as exc: print(f"invalid JSON: {exc}",file=sys.stderr); return 2
    errors=validate(data)
    if errors:
        for x in errors: print("ERROR:",x,file=sys.stderr)
        return 1
    print(f"ReflexBench submission envelope: PASS ({args.submission})")
    return 0
if __name__ == "__main__": raise SystemExit(main())

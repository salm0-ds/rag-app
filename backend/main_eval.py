"""
Generation eval: score saved RAG outputs, track results across runs, flag regressions.

Exit codes: 0 = ok, 1 = regression or too many failed scores, 2 = the eval itself crashed.
"""
import asyncio
import json
import logging
import math
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from openai import AsyncOpenAI
from ragas.embeddings.base import embedding_factory
from ragas.llms import llm_factory
from ragas.metrics.collections import AnswerCorrectness, AnswerRelevancy, Faithfulness

from config import settings

log = logging.getLogger("rag_eval")

# ----------------------------------------------------------------------------- config
input_address = settings.INPUT_EVAL_DATA_ADD     # queries + references (frozen, human-reviewed)
output_address = settings.OUTPUT_EVAL_DATA_ADD   # app answers + retrieved context
dataset_path = settings.DATASET_PATH             # each run gets its own folder in here
api_key = settings.OPENAI_API_KEY
eval_model = settings.EVAL_MODEL
embed_provider = settings.EMBED_PROVIDER
eval_embed_model = settings.EVAL_EMBED_MODEL
HISTORY_PATH = Path("backend/evals/datasets/scores_history.jsonl")  # one line per run, append-only

METRICS = ["faithfulness", "correctness", "relevance"]
CONCURRENCY = 5               # rows scored at the same time
REGRESSION_TOLERANCE = 0.03   # a drop bigger than this vs the previous run is a problem (judge noise is ~0.01-0.02)
MAX_FAILURE_RATE = 0.05       # if >5% of judge scores fail, this run's means can't be trusted


# ----------------------------------------------------------------------------- setup
def setup_logging(run_dir: Path) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[logging.StreamHandler(), logging.FileHandler(run_dir / "eval.log", encoding="utf-8")],
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)  # one INFO line per API call is noise


@dataclass
class Judge:
    faithfulness: Faithfulness
    correctness: AnswerCorrectness
    relevance: AnswerRelevancy


def build_judge() -> Judge:
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    # the client retries rate limits and transient errors for us
    client = AsyncOpenAI(api_key=api_key, max_retries=5, timeout=60)
    llm = llm_factory(eval_model, client=client)
    embeddings = embedding_factory(embed_provider, model=eval_embed_model, client=client)
    return Judge(
        faithfulness=Faithfulness(llm=llm),
        correctness=AnswerCorrectness(llm=llm, embeddings=embeddings),
        relevance=AnswerRelevancy(llm=llm, embeddings=embeddings),
    )


def git_sha() -> str | None:
    try:
        sha = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True, stderr=subprocess.DEVNULL).strip()
        dirty = subprocess.check_output(["git", "status", "--porcelain"], text=True, stderr=subprocess.DEVNULL).strip()
        return sha + ("-dirty" if dirty else "")
    except Exception:
        return None


# ----------------------------------------------------------------------------- load
def parse_context(ctx) -> list[str]:
    """CSV stores the retrieved chunks as text; the judge needs a list of strings."""
    if ctx is None or (isinstance(ctx, float) and math.isnan(ctx)):
        return []
    if isinstance(ctx, list):
        return [str(c) for c in ctx]
    try:
        value = json.loads(ctx)
        if isinstance(value, list):
            return [str(c) for c in value]
    except (TypeError, ValueError):
        pass
    log.warning("context is not a JSON list; scoring it as one chunk (faithfulness may be distorted)")
    return [str(ctx)]


def _require_columns(df: pd.DataFrame, columns: set[str], name: str) -> None:
    missing = columns - set(df.columns)
    if missing:
        raise ValueError(f"{name} is missing columns {sorted(missing)}; it has {list(df.columns)}")


def load_eval_data(queries_path: str, outputs_path: str) -> pd.DataFrame:
    df_query = pd.read_csv(queries_path)
    df_output = pd.read_csv(outputs_path)
    _require_columns(df_query, {"user_query", "reference"}, queries_path)
    _require_columns(df_output, {"user_query", "context", "output"}, outputs_path)

    # join on the query text instead of trusting row order; validate= raises on duplicate queries
    df = df_query[["user_query", "reference"]].merge(
        df_output[["user_query", "context", "output"]], on="user_query", how="inner", validate="one_to_one"
    )
    if len(df) == 0 or len(df) != len(df_query) or len(df) != len(df_output):
        raise ValueError(
            f"queries and outputs don't line up: {len(df_query)} queries, {len(df_output)} outputs, {len(df)} matched. "
            "Regenerate the outputs file from the current queries file."
        )
    log.info("loaded %d rows", len(df))
    return df


# ----------------------------------------------------------------------------- score
async def safe(name: str, coro):
    """A failed judge call becomes None (excluded from means and counted), never a crash and never a fake 0."""
    try:
        v = float((await coro).value)
        if math.isnan(v):
            raise ValueError("judge returned NaN")
        return v
    except Exception as e:
        log.warning("%s judge call failed: %s: %s", name, type(e).__name__, str(e)[:150])
        return None


async def generation_eval(judge: Judge, user_query: str, response: str, reference: str, context) -> dict:
    contexts = parse_context(context)
    f_result, ac_result, r_result = await asyncio.gather(
        safe("faithfulness", judge.faithfulness.ascore(user_input=user_query, response=response, retrieved_contexts=contexts)),
        safe("correctness", judge.correctness.ascore(user_input=user_query, response=response, reference=reference)),
        safe("relevance", judge.relevance.ascore(user_input=user_query, response=response)),
    )
    return {"user_query": user_query, "faithfulness": f_result, "correctness": ac_result, "relevance": r_result}


async def score_row(judge: Judge, row: dict, sem: asyncio.Semaphore) -> dict:
    async with sem:
        try:
            if pd.isna(row["output"]) or not str(row["output"]).strip():
                raise ValueError("app produced no output for this query")
            return await generation_eval(judge, row["user_query"], row["output"], row["reference"], row["context"])
        except Exception:
            log.exception("row failed, scoring as missing: %.80s", row["user_query"])
            return {"user_query": row["user_query"], **{m: None for m in METRICS}}


async def gen_eval_scores(df: pd.DataFrame, judge: Judge) -> pd.DataFrame:
    log.info("scoring %d rows (concurrency %d)", len(df), CONCURRENCY)
    sem = asyncio.Semaphore(CONCURRENCY)
    rows = await asyncio.gather(*(score_row(judge, r, sem) for r in df.to_dict("records")))
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------- summarise + history
def calculate_mean(scores: pd.DataFrame, run_id: str, dataset_hash: str) -> dict:
    nums = scores[METRICS].apply(pd.to_numeric, errors="coerce")
    means = {m: (None if pd.isna(v) else round(float(v), 4)) for m, v in nums.mean().items()}  # None, not NaN: valid JSON
    return {
        "date": run_id, **means,
        "n_rows": len(scores),
        "n_failed": int(nums.isna().sum().sum()),   # failed judge scores; high = means rest on little data
        "dataset_hash": dataset_hash,               # only runs on the same dataset are comparable
        "git_sha": git_sha(),
        "judge_model": eval_model,
    }


def load_history(path: Path) -> list[dict]:
    if not path.exists():
        return []
    records = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            log.warning("skipping corrupt history line %d in %s", i, path)
    return records


def append_history(path: Path, record: dict) -> None:
    # append-only: a crash can damage at most the last line, never the earlier history
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def find_previous(record: dict, history: list[dict]) -> dict | None:
    same_dataset = [h for h in history if h.get("dataset_hash") == record["dataset_hash"]]
    if not same_dataset:
        log.warning("no previous run on this dataset: first run, or the dataset changed. Skipping comparison.")
    return same_dataset[-1] if same_dataset else None


def find_problems(record: dict, previous: dict | None) -> list[str]:
    problems = []
    total = max(record["n_rows"] * len(METRICS), 1)
    if record["n_failed"] / total > MAX_FAILURE_RATE:
        problems.append(f"{record['n_failed']}/{total} judge scores failed (max {MAX_FAILURE_RATE:.0%}); means are unreliable")
    for m in METRICS:
        cur = record[m]
        if cur is None:
            problems.append(f"{m}: no valid scores at all")
        elif previous and previous.get(m) is not None and previous[m] - cur > REGRESSION_TOLERANCE:
            problems.append(f"{m} dropped {previous[m]:.3f} -> {cur:.3f} (tolerance {REGRESSION_TOLERANCE})")
    return problems


# ----------------------------------------------------------------------------- report
def print_report(record: dict, previous: dict | None, problems: list[str]) -> None:
    print(f"\n=== eval {record['date']} | git {record['git_sha']} | {record['n_rows']} rows | judge {record['judge_model']}")
    for m in METRICS:
        cur, prev = record[m], previous.get(m) if previous else None
        cur_s = "n/a" if cur is None else f"{cur:.3f}"
        delta = f"{cur - prev:+.3f}" if cur is not None and prev is not None else "n/a"
        print(f"{m:<14}{cur_s:>8}   change vs previous run: {delta}")
    print(f"failed judge scores: {record['n_failed']}")
    for p in problems:
        print(f"PROBLEM: {p}")
    print("RESULT:", "FAIL" if problems else "OK")


def plot_score_trends(history: list[dict], out_path: Path, last_n: int = 15) -> None:
    """Trend chart: runs evenly spaced in date order, date as the label."""
    if not history:
        log.info("no history to plot")
        return
    df = pd.DataFrame(history)
    df["date"] = pd.to_datetime(df["date"], format="%Y%m%d-%H%M%S")
    df = df.sort_values("date").tail(last_n).reset_index(drop=True)

    x_axis = list(range(len(df)))
    labels = df["date"].dt.strftime("%d %b %H:%M")

    plt.figure(figsize=(10, 5))
    for col in METRICS:
        if col in df:
            plt.plot(x_axis, pd.to_numeric(df[col], errors="coerce"), marker="o", linewidth=2, label=col)
    plt.xticks(x_axis, labels, rotation=45, ha="right")
    plt.title("RAG evaluation score trends", fontsize=14, fontweight="bold")
    plt.xlabel("Evaluation run", fontsize=11)
    plt.ylabel("Score", fontsize=11)
    plt.ylim(-0.05, 1.05)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend(loc="lower left", fontsize=10)
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()


# ----------------------------------------------------------------------------- orchestration
async def run_eval() -> int:
    run_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = Path(dataset_path) / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    setup_logging(run_dir)
    log.info("run %s started", run_id)

    judge = build_judge()
    df = load_eval_data(input_address, output_address)
    scores = await gen_eval_scores(df, judge)
    scores.to_csv(run_dir / "eval_scores.csv", index=False)

    dataset_hash = sha256(Path(input_address).read_bytes()).hexdigest()[:12]
    record = calculate_mean(scores, run_id, dataset_hash)
    (run_dir / "summary.json").write_text(json.dumps(record, indent=2), encoding="utf-8")

    history = load_history(HISTORY_PATH)
    previous = find_previous(record, history)
    problems = find_problems(record, previous)
    append_history(HISTORY_PATH, record)   # recorded even when it fails, so bad runs show up in the trend
    history.append(record)

    print_report(record, previous, problems)
    try:
        plot_score_trends(history, run_dir / "trend.png")
    except Exception:
        log.exception("plotting failed (non-critical)")

    log.info("run %s finished: %s", run_id, "FAIL" if problems else "OK")
    return 1 if problems else 0


async def main() -> int:
    try:
        return await run_eval()
    except Exception:
        log.exception("eval crashed")
        return 2


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
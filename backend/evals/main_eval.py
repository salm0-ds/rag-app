import asyncio
from ragas import experiment, Dataset
from ragas.metrics import discrete_metric, MetricResult

@discrete_metric(name="intent_metric", allowed_values=["pass", "fail"])
def check_intent(llm_answer: str, ground_truth: str):
    if llm_answer.strip().lower() == ground_truth.strip().lower():
        return MetricResult(value="pass", reason="Exact intent match")
    return MetricResult(value="fail", reason="Incorrect intent match")

@experiment()
async def experiment1(row):
    result = await check_intent.ascore(
        llm_answer=row["output"],
        ground_truth=row["ground_truth"],
    )
    return {**row, "score": result.value, "reason": result.reason}

async def main():
    # Expects evaluation/datasets/test_dataset2.csv
    dataset = Dataset.load(
        name="golden_dataset",
        backend="local/csv",
        root_dir="evals",
    )
    results = await experiment1.arun(dataset)
    print("results:", results)

if __name__ == "__main__":
    asyncio.run(main())
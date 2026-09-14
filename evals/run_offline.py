import argparse
import json
import os
from pathlib import Path
from statistics import mean

from deepeval import evaluate
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase, LLMTestCaseParams
from ragas import EvaluationDataset, SingleTurnSample
from ragas import evaluate as ragas_evaluate
from ragas.llms import llm_factory
from ragas.metrics import Faithfulness, ResponseRelevancy

ROOT = Path(__file__).resolve().parent.parent


def load_cases(dataset_dir: Path) -> list[dict]:
    rows: list[dict] = []
    for path in sorted(dataset_dir.glob("*.jsonl")):
        with path.open(encoding="utf-8") as file:
            rows.extend(json.loads(line) for line in file if line.strip())
    return rows


def run(rows: list[dict], threshold: float) -> dict:
    judge_model = os.environ.get("LLM_JUDGE_MODEL", "gpt-4.1")
    answer_quality = GEval(
        name="answer_quality",
        model=judge_model,
        criteria="答案应正确、完整、简洁，遵守上下文中的业务规则与安全边界。",
        evaluation_params=[
            LLMTestCaseParams.INPUT,
            LLMTestCaseParams.ACTUAL_OUTPUT,
            LLMTestCaseParams.EXPECTED_OUTPUT,
            LLMTestCaseParams.RETRIEVAL_CONTEXT,
        ],
        threshold=threshold,
    )
    cases = [
        LLMTestCase(
            input=row["input"],
            actual_output=row["actual_output"],
            expected_output=row["expected_output"],
            retrieval_context=row["retrieval_context"],
        )
        for row in rows
    ]
    deepeval_result = evaluate(cases, [answer_quality])
    geval_scores = [result.metrics_data[0].score for result in deepeval_result.test_results]

    ragas_dataset = EvaluationDataset(
        samples=[
            SingleTurnSample(
                user_input=row["input"],
                response=row["actual_output"],
                retrieved_contexts=row["retrieval_context"],
                reference=row["expected_output"],
            )
            for row in rows
        ]
    )
    ragas_result = ragas_evaluate(
        dataset=ragas_dataset,
        metrics=[Faithfulness(), ResponseRelevancy()],
        llm=llm_factory(judge_model),
    )
    ragas_rows = ragas_result.to_pandas().to_dict(orient="records")
    summary = {
        "count": len(rows),
        "geval_answer_quality": mean(geval_scores),
        "ragas_faithfulness": mean(float(row["faithfulness"]) for row in ragas_rows),
        "ragas_response_relevancy": mean(float(row["answer_relevancy"]) for row in ragas_rows),
        "threshold": threshold,
    }
    summary["passed"] = all(summary[key] >= threshold for key in (
        "geval_answer_quality", "ragas_faithfulness", "ragas_response_relevancy"
    ))
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-dir", type=Path, default=ROOT / "evals" / "datasets")
    parser.add_argument("--output", type=Path, default=ROOT / "evals" / "results" / "offline.json")
    parser.add_argument("--threshold", type=float, default=0.75)
    args = parser.parse_args()
    result = run(load_cases(args.dataset_dir), args.threshold)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())


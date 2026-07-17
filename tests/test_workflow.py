import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.run_workflow import WorkflowError, build_fact_ledger, run_pipeline  # noqa: E402


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.project = json.loads((ROOT / "examples" / "project_input.json").read_text(encoding="utf-8"))

    def test_prompt_only_pipeline_writes_complete_package(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            state = run_pipeline(self.project, output)
            self.assertEqual(state["current_state"], "QA_COMPLETE")
            self.assertFalse(state["media_rendered"])
            expected = {
                "fact_ledger.json",
                "creative_brief.json",
                "script_package.json",
                "storyboard.json",
                "generation_prompt.txt",
                "render_job.json",
                "qa_report.json",
                "state.json",
            }
            self.assertEqual(expected, {path.name for path in output.iterdir()})
            render_job = json.loads((output / "render_job.json").read_text(encoding="utf-8"))
            self.assertEqual(render_job["status"], "PROMPT_READY")
            self.assertIsNone(render_job["media"])

    def test_unverified_claim_is_excluded_from_every_generated_artifact(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            run_pipeline(self.project, output)
            ledger = json.loads((output / "fact_ledger.json").read_text(encoding="utf-8"))
            capacity = next(item for item in ledger["entries"] if item["id"] == "large-capacity")
            self.assertFalse(capacity["usable"])
            generated = "\n".join(path.read_text(encoding="utf-8") for path in output.iterdir())
            self.assertNotIn("very large capacity", generated.lower().replace(capacity["text"].lower(), ""))

    def test_resume_returns_existing_completed_state(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            first = run_pipeline(self.project, output)
            second = run_pipeline(self.project, output, resume=True)
            self.assertEqual(first, second)

    def test_risky_verified_claim_is_not_usable(self):
        self.project["product"]["facts"] = [
            {"id": "miracle", "text": "Guaranteed miracle results.", "source": "user_supplied"}
        ]
        with self.assertRaises(WorkflowError):
            build_fact_ledger(self.project)

    def test_schema_files_are_valid_json(self):
        for path in (ROOT / "schemas").glob("*.json"):
            parsed = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(parsed["$schema"], "https://json-schema.org/draft/2020-12/schema")

    def test_hazardous_tool_copy_is_category_relevant_and_safety_guarded(self):
        project = json.loads((ROOT / "examples" / "hazardous_tool_input.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            state = run_pipeline(project, output)
            self.assertEqual(state["current_state"], "QA_COMPLETE")
            generated = "\n".join(path.read_text(encoding="utf-8") for path in output.iterdir()).lower()
            for phrase in ("small essentials", "big tote", "errand bag", "phone and keys", "for errands"):
                self.assertNotIn(phrase, generated)
            for safety_term in ("eye protection", "work gloves", "workpiece", "no tool near", "no free hand"):
                self.assertIn(safety_term, generated)
            self.assertNotIn("hold the product beside the face", generated)

            report = json.loads((output / "qa_report.json").read_text(encoding="utf-8"))
            checks = {item["id"]: item["status"] for item in report["automatic_checks"]}
            self.assertEqual(checks["category-relevance"], "PASS")
            self.assertEqual(checks["hazardous-tool-safety"], "PASS")


if __name__ == "__main__":
    unittest.main()

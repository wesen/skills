import json
from pathlib import Path
import sys
import tempfile
import unittest

SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))
from render_report import render, validate  # noqa: E402


FIXTURE = SCRIPT_DIR / "fixtures" / "minimal.json"


class RenderReportTest(unittest.TestCase):
    def model(self):
        return json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_renders_required_sections(self):
        output = render(self.model())
        for heading in (
            "Conversation turns",
            "Session timeline",
            "Current classified knowledge",
            "Files inspected or analyzed",
            "Files edited or created",
            "API and package inventory",
            "Repository and report state",
        ):
            self.assertIn(heading, output)

    def test_escapes_model_values(self):
        model = self.model()
        model["title"] = "<script>alert('x')</script>"
        output = render(model)
        self.assertNotIn("<script>alert", output)
        self.assertIn("&lt;script&gt;", output)

    def test_churn_requires_prevention_advice(self):
        model = self.model()
        model["timeline"][1]["advice"] = []
        with self.assertRaisesRegex(ValueError, "requires prevention advice"):
            validate(model)

    def test_writes_standalone_html(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.html"
            output.write_text(render(self.model()), encoding="utf-8")
            data = output.read_text(encoding="utf-8")
            self.assertTrue(data.startswith("<!doctype html>"))
            self.assertIn("<style>", data)
            self.assertNotIn("https://", data)


if __name__ == "__main__":
    unittest.main()

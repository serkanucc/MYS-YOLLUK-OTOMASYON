import importlib.util
from pathlib import Path
import sys

runner_path = Path(__file__).resolve().parents[1] / "scripts" / "stage1-live-run.py"
sys.path.insert(0, str(runner_path.parent))
spec = importlib.util.spec_from_file_location("stage1_live_run", runner_path)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)

assert runner.should_skip_assignment({"status": "SIMULATED_COMPLETED"}) is False
assert runner.should_skip_assignment({"status": "STAGE1_COMPLETED"}) is True
assert runner.should_skip_assignment({"status": "STAGE1_COMPLETED"}, force_form_test=True) is False
assert runner.should_skip_assignment({"status": "PROCESSING"}) is False

print("STAGE1 RUNNER POLICY TESTS OK")

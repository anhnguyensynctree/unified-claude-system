"""Tests for oms-brief.py — daily brief building and metrics parsing."""
import json
from pathlib import Path


class TestCountStatuses:
    def test_counts_all_statuses(self, brief_module, tmp_queue):
        counts = brief_module.count_statuses(tmp_queue)
        assert counts["done"] == 2
        assert counts["queued"] == 1
        assert counts["cto-stop"] == 1
        assert counts["in-progress"] == 0

    def test_missing_file_returns_zeros(self, brief_module, tmp_path):
        counts = brief_module.count_statuses(tmp_path / "nonexistent.md")
        assert all(v == 0 for v in counts.values())

    def test_empty_file_returns_zeros(self, brief_module, tmp_path):
        f = tmp_path / "empty.md"
        f.write_text("")
        counts = brief_module.count_statuses(f)
        assert all(v == 0 for v in counts.values())


class TestReadProjectMetrics:
    def test_parses_costs_with_model_data(self, brief_module, tmp_project, tmp_costs):
        m = brief_module.read_project_metrics(tmp_project)
        assert m["tasks_run"] == 3
        assert m["passed"] == 2
        assert m["failed"] == 1
        assert m["first_pass_count"] == 1
        assert m["total_cost"] == 0.06
        assert m["model_counts"] == {"qwen": 2, "haiku": 1}
        assert m["model_pass"] == {"qwen": 2}
        assert m["model_fail"] == {"haiku": 1}
        assert m["fail_at_counts"] == {"cto": 1}

    def test_missing_costs_returns_empty(self, brief_module, tmp_path):
        assert brief_module.read_project_metrics(tmp_path) == {}

    def test_empty_costs_returns_empty(self, brief_module, tmp_project):
        (tmp_project / ".claude" / "oms-costs.json").write_text("[]")
        assert brief_module.read_project_metrics(tmp_project) == {}

    def test_handles_missing_model_used(self, brief_module, tmp_project):
        costs = [{"task_id": "T-1", "cost_usd": 0.01, "passed": True,
                  "first_pass": True, "validators": "dev✓"}]
        (tmp_project / ".claude" / "oms-costs.json").write_text(json.dumps(costs))
        m = brief_module.read_project_metrics(tmp_project)
        assert m["model_counts"] == {"unknown": 1}


class TestBuildBrief:
    def test_full_brief_structure(self, brief_module, tmp_path, tmp_config, tmp_project, tmp_queue, tmp_costs):
        _, config = tmp_config
        brief = brief_module.build_brief(config)

        # Header
        assert "**OMS Daily Brief**" in brief
        # Summary line
        assert "done" in brief
        assert "queued" in brief
        assert "stopped" in brief
        # Project appears
        assert "test-project" in brief
        # Cost data
        assert "$" in brief
        # Needs attention section (has stopped tasks)
        assert "Needs attention" in brief
        # Model routing
        assert "LLM Router" in brief
        # Failure analysis
        assert "Failure stages" in brief
        assert "cto" in brief

    def test_skips_inactive_projects(self, brief_module, tmp_config):
        _, config = tmp_config
        brief = brief_module.build_brief(config)
        assert "inactive" not in brief.lower().split("idle")[0]  # not in project lines

    def test_idle_projects_listed(self, brief_module, tmp_config):
        _, config = tmp_config
        brief = brief_module.build_brief(config)
        assert "Idle" in brief
        assert "idle-project" in brief

    def test_empty_config(self, brief_module):
        brief = brief_module.build_brief({"projects": {}})
        assert "**OMS Daily Brief**" in brief
        assert "0 total" in brief

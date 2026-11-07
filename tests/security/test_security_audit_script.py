# tests/security/test_security_audit_script.py
# Kiem logic lenh audit T092 bang runner gia: dung o lenh loi dau tien, bang PASS/FAIL, lo hong chap nhan co ly do.
import importlib.util
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path
from types import ModuleType

import pytest

AUDIT_SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "security_audit.py"


def load_audit_module() -> ModuleType:
    module_spec = importlib.util.spec_from_file_location("security_audit", AUDIT_SCRIPT)
    assert module_spec is not None and module_spec.loader is not None
    audit_module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(audit_module)
    return audit_module


@pytest.fixture(scope="module")
def audit() -> ModuleType:
    return load_audit_module()


class ScriptedRunner:
    def __init__(self, outcomes: dict[str, tuple[int, str]]) -> None:
        self._outcomes = outcomes
        self.commands: list[tuple[str, ...]] = []

    def __call__(self, command: Sequence[str]) -> tuple[int, str]:
        self.commands.append(tuple(command))
        return self._outcomes.get(command[0], (0, "ok"))


def test_check_stops_at_first_failing_command(audit: ModuleType) -> None:
    check = audit.AuditCheck(
        "export roi audit", "lo hong dependency", (("export",), ("audit",))
    )
    runner = ScriptedRunner({"export": (2, "loi export lock")})

    result = audit.run_check(check, runner)

    assert result.passed is False
    assert "loi export lock" in result.detail
    assert runner.commands == [("export",)]


def test_report_marks_each_check_pass_or_fail(audit: ModuleType) -> None:
    passing = audit.AuditCheck("tests", "rollback", (("pytest",),))
    failing = audit.AuditCheck("npm", "lo hong dependency", (("npm",),))
    runner = ScriptedRunner({"npm": (1, "found 1 high severity vulnerability")})

    report = audit.render_report(audit.run_audit([passing, failing], runner))

    assert "| tests | rollback | PASS |" in report
    assert (
        "| npm | lo hong dependency | FAIL | found 1 high severity vulnerability |"
        in report
    )


def test_every_accepted_vulnerability_has_a_reason_and_is_ignored(
    audit: ModuleType, tmp_path: Path
) -> None:
    _, audit_command = audit.pip_audit_commands("ai", tmp_path / "ai.txt")

    for vulnerability_id, reason in audit.ACCEPTED_VULNERABILITIES.items():
        assert reason.strip()
        ignored_index = audit_command.index(vulnerability_id)
        assert audit_command[ignored_index - 1] == "--ignore-vuln"


def test_api_audit_includes_serving_dependencies(
    audit: ModuleType, tmp_path: Path
) -> None:
    # Ban production cai extra serving (torch, MediaPipe) nen phai quet ca nhom nay
    export_command, _ = audit.pip_audit_commands(
        "services/inference-api", tmp_path / "api.txt"
    )
    (test_command,) = audit.build_checks(tmp_path)[0].commands

    assert export_command[-2:] == ("--extra", "serving")
    # Thieu extra serving thi test GRU bi skip im lang ma audit van PASS
    serving_index = test_command.index("serving")
    assert test_command[serving_index - 1] == "--extra"


def test_audit_tools_are_pinned(audit: ModuleType, tmp_path: Path) -> None:
    # Phien ban co dinh: ket qua tai lap duoc; detect-secrets khac phien ban se ghi de baseline
    tool_commands = [
        command
        for check in audit.build_checks(tmp_path)
        for command in check.commands
        if "tool" in command
    ]

    assert len(tool_commands) == 3
    for command in tool_commands:
        pinned_tool = command[command.index("--from") + 1]
        assert "==" in pinned_tool


def test_secret_scan_covers_files_about_to_be_committed(
    audit: ModuleType, tmp_path: Path
) -> None:
    # Audit chay truoc commit phai quet ca file moi chua add, nhung bo qua file trong .gitignore
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / ".gitignore").write_text("bo-qua.txt\n", encoding="utf-8")
    (tmp_path / "moi.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "bo-qua.txt").write_text("y\n", encoding="utf-8")
    (tmp_path / audit.SECRETS_BASELINE).write_text("{}\n", encoding="utf-8")

    assert audit.repository_files(tmp_path) == [".gitignore", "moi.py"]


def test_tool_result_is_summarized_after_installer_noise(audit: ModuleType) -> None:
    # uv in "Installed N packages" ra stderr khi tu cai extra; dong tom tat phai la ket qua cua cong cu
    noisy_tool = (
        sys.executable,
        "-c",
        "import sys; print('415 passed'); print('Installed 34 packages', file=sys.stderr)",
    )

    return_code, output = audit.run_subprocess(noisy_tool)

    assert return_code == 0
    assert audit.summary_line(output) == "415 passed"


def test_summary_ignores_git_warnings(audit: ModuleType) -> None:
    hook_output = "warning: in the working copy of 'a.py', LF will be replaced by CRLF"

    assert audit.summary_line(hook_output) == "ok, khong co phat hien moi"
    assert audit.summary_line(hook_output + "\n411 passed") == "411 passed"

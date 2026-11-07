# scripts/security_audit.py
# Lenh audit bao mat mot lan cho BGK va CI (T092, FR-027): chay test bao mat/privacy/loi/phuc hoi, quet lo hong
# dependency (pip-audit API + AI, npm audit production) va quet secret theo baseline da duyet; in bang PASS/FAIL.
import importlib.util
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SECRETS_BASELINE = ".secrets.baseline"
OUTPUT_TAIL_CHARS = 160
COMMAND_NOT_FOUND = 127
# Ghim phien ban cong cu: ket qua tai lap duoc; detect-secrets khac phien ban baseline se ghi de baseline
PIP_AUDIT_TOOL = "pip-audit==2.10.1"
DETECT_SECRETS_TOOL = "detect-secrets==1.5.0"  # pragma: allowlist secret
# Lo hong da danh gia la khong khai thac duoc luc runtime (docs/security-report.md); xem lai moi lan nang lock
ACCEPTED_VULNERABILITIES = {
    "PYSEC-2025-194": "torch.jit.script, API khong dung TorchScript",
    "PYSEC-2026-3447": "setuptools dong goi sdist tren macOS, khong chay luc runtime",
    "GHSA-xmj3-9gf7-h52w": "setuptools cai wheel kieu egg tren Windows, khong chay luc runtime",
}


@dataclass(frozen=True)
class AuditCheck:
    name: str
    requirement: str
    commands: tuple[tuple[str, ...], ...]


@dataclass(frozen=True)
class CheckResult:
    check: AuditCheck
    passed: bool
    detail: str


CommandRunner = Callable[[Sequence[str]], tuple[int, str]]


def uv_command() -> list[str]:
    # CI co uv tren PATH; may Windows cua nhom chay uv qua module cua Python he thong
    installed_uv = shutil.which("uv")
    if installed_uv:
        return [installed_uv]
    if importlib.util.find_spec("uv") is not None:
        return [sys.executable, "-m", "uv"]
    # Khong co uv: lenh se bao FAIL ro rang thay vi lam vo audit
    return ["uv"]


def pip_audit_commands(project: str, export_path: Path) -> tuple[tuple[str, ...], ...]:
    export_command = [
        *uv_command(),
        "export",
        "--project",
        project,
        "--locked",
        "--format",
        "requirements-txt",
        "--no-hashes",
        "--no-emit-project",
        "--no-emit-package",
        "visign-ai",
        "--no-dev",
        "-o",
        str(export_path),
    ]
    if project == "services/inference-api":
        export_command += ["--extra", "serving"]
    ignored = [
        argument
        for vulnerability in ACCEPTED_VULNERABILITIES
        for argument in ("--ignore-vuln", vulnerability)
    ]
    audit_command = [
        *uv_command(),
        "tool",
        "run",
        "--from",
        PIP_AUDIT_TOOL,
        "pip-audit",
        "-r",
        str(export_path),
        "--no-deps",
        "--disable-pip",
        "--progress-spinner",
        "off",
        *ignored,
    ]
    return (tuple(export_command), tuple(audit_command))


def repository_files(root: Path = REPOSITORY_ROOT) -> list[str]:
    # File da track va file moi chua add (tru file bi .gitignore): audit truoc commit thay dung thu se duoc commit
    listing = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )
    return sorted(
        path
        for path in set(listing.stdout.splitlines())
        if path != SECRETS_BASELINE and (root / path).is_file()
    )


def build_checks(work_directory: Path) -> list[AuditCheck]:
    npm = shutil.which("npm") or "npm"
    # Chay voi extra serving nhu ban production; thieu extra thi test GRU bi skip im lang
    test_command = (
        *uv_command(),
        "run",
        "--project",
        "services/inference-api",
        "--extra",
        "serving",
        "pytest",
        "services/inference-api/tests",
        "tests/contract",
        "tests/integration",
        "tests/security",
        "-q",
    )
    secret_command = (
        *uv_command(),
        "tool",
        "run",
        "--from",
        DETECT_SECRETS_TOOL,
        "python",
        "-m",
        "detect_secrets.pre_commit_hook",
        "--baseline",
        SECRETS_BASELINE,
        *repository_files(),
    )
    return [
        AuditCheck(
            "Test bao mat, privacy, loi, phuc hoi",
            "video/secret, log an toan, timeout, gioi han, rollback",
            (test_command,),
        ),
        AuditCheck(
            "pip-audit API (gom serving)",
            "lo hong dependency",
            pip_audit_commands("services/inference-api", work_directory / "api.txt"),
        ),
        AuditCheck(
            "pip-audit AI",
            "lo hong dependency",
            pip_audit_commands("ai", work_directory / "ai.txt"),
        ),
        AuditCheck(
            "npm audit web production",
            "lo hong dependency",
            (
                (
                    npm,
                    "audit",
                    "--prefix",
                    "apps/web",
                    "--omit=dev",
                    "--audit-level=high",
                ),
            ),
        ),
        AuditCheck(
            "Quet secret theo baseline", "khong co secret trong repo", (secret_command,)
        ),
    ]


def run_subprocess(command: Sequence[str]) -> tuple[int, str]:
    # check=False: ma thoat khac 0 la ket qua FAIL can bao cao, khong phai loi cua chinh lenh audit
    try:
        completed = subprocess.run(
            list(command),
            cwd=REPOSITORY_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except FileNotFoundError:
        return COMMAND_NOT_FOUND, f"Khong tim thay lenh: {command[0]}"
    # stdout dat sau cung: dong cuoi la ket qua cua cong cu, khong phai log cai dat cua uv tren stderr
    return completed.returncode, (completed.stderr + completed.stdout).strip()


def run_check(check: AuditCheck, runner: CommandRunner) -> CheckResult:
    output = ""
    for command in check.commands:
        return_code, output = runner(command)
        if return_code != 0:
            return CheckResult(check, False, output[-OUTPUT_TAIL_CHARS:])
    return CheckResult(check, True, summary_line(output)[-OUTPUT_TAIL_CHARS:])


def summary_line(output: str) -> str:
    # Bo canh bao cua git (CRLF) de dong tom tat la ket qua that cua cong cu
    meaningful_lines = [
        line
        for line in output.splitlines()
        if line.strip() and not line.startswith("warning:")
    ]
    return meaningful_lines[-1] if meaningful_lines else "ok, khong co phat hien moi"


def render_report(results: Sequence[CheckResult]) -> str:
    lines = ["| Kiem tra | Yeu cau FR-027 | Ket qua | Chi tiet |", "|---|---|---|---|"]
    for result in results:
        verdict = "PASS" if result.passed else "FAIL"
        detail = result.detail.replace("|", "/").replace("\n", " ")
        lines.append(
            f"| {result.check.name} | {result.check.requirement} | {verdict} | {detail} |"
        )
    return "\n".join(lines)


def run_audit(checks: Sequence[AuditCheck], runner: CommandRunner) -> list[CheckResult]:
    results = []
    for check in checks:
        print(f"[INFO] Dang chay: {check.name}", flush=True)
        results.append(run_check(check, runner))
    return results


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="visign-audit-") as work_directory:
        results = run_audit(build_checks(Path(work_directory)), run_subprocess)
    print(render_report(results))
    failed = [result.check.name for result in results if not result.passed]
    if failed:
        print(f"[ERROR] Audit chua dat: {', '.join(failed)}")
        return 1
    print("[SUCCESS] Audit bao mat dat toan bo kiem tra")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

import subprocess
from dataclasses import dataclass


@dataclass
class ExecutionResult:
    success: bool
    exit_code: int
    stdout: str
    stderr: str


class Executor:

    @staticmethod
    def run(command: str) -> ExecutionResult:

        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
        )

        return ExecutionResult(
            success=result.returncode == 0,
            exit_code=result.returncode,
            stdout=result.stdout.strip(),
            stderr=result.stderr.strip(),
        )
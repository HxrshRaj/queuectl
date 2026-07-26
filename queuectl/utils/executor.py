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
    def execute(command: str) -> ExecutionResult:

        process = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
        )

        return ExecutionResult(
            success=process.returncode == 0,
            exit_code=process.returncode,
            stdout=process.stdout.strip(),
            stderr=process.stderr.strip(),
        )
"""Shell tools."""

import asyncio
import os
import subprocess
from typing import Optional, List, Dict, Any


class ExecTool:
    """Tool for executing shell commands."""

    name = "exec"
    description = "Execute a shell command"
    parameters = {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "Command to execute"
            },
            "blocking": {
                "type": "boolean",
                "description": "Whether to wait for the command to complete"
            },
            "requires_approval": {
                "type": "boolean",
                "description": "Whether the command requires user approval"
            }
        },
        "required": ["command"]
    }

    def __init__(
        self,
        working_dir: str,
        timeout: int = 60,
        restrict_to_workspace: bool = False,
        sandbox: bool = False,
        path_append: Optional[str] = None,
        allowed_env_keys: Optional[List[str]] = None,
    ):
        self.working_dir = working_dir
        self.timeout = timeout
        self.restrict_to_workspace = restrict_to_workspace
        self.sandbox = sandbox
        self.path_append = path_append
        self.allowed_env_keys = allowed_env_keys or []

    async def run(self, command: str, blocking: bool = True, requires_approval: bool = False) -> str:
        """Run the tool."""
        if requires_approval:
            return "Error: Command requires approval, which is not supported in this environment"

        env = os.environ.copy()
        if self.path_append:
            env["PATH"] = f"{env.get('PATH', '')};{self.path_append}" if os.name == "nt" else f"{env.get('PATH', '')}:{self.path_append}"

        # Filter environment variables
        if self.allowed_env_keys:
            filtered_env = {k: v for k, v in env.items() if k in self.allowed_env_keys}
            # Always include PATH
            filtered_env["PATH"] = env.get("PATH", "")
            env = filtered_env

        try:
            if blocking:
                result = await asyncio.create_subprocess_shell(
                    command,
                    cwd=self.working_dir,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                stdout, stderr = await asyncio.wait_for(
                    result.communicate(), timeout=self.timeout
                )
                output = stdout.strip()
                if stderr:
                    output += f"\n\nSTDERR:\n{stderr.strip()}"
                return output
            else:
                # Non-blocking execution
                process = await asyncio.create_subprocess_shell(
                    command,
                    cwd=self.working_dir,
                    env=env,
                )
                return f"Command started in background with PID: {process.pid}"
        except asyncio.TimeoutError:
            return f"Error: Command timed out after {self.timeout} seconds"
        except Exception as e:
            return f"Error executing command: {str(e)}"

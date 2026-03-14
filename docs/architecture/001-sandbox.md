# Architecture Decision Record: Execution Sandbox

## Context
JARVIS-X is an autonomous agent with the ability to execute shell commands on the host machine. To protect the host operating system from destructive prompt injection or LLM hallucinations, we needed an isolation mechanism for code execution.

## Decision
We chose **Docker** as the primary execution sandbox instead of native Python `subprocess` restrictions, virtual environments, or `pyjail` variants. 

The `SystemCommandTool` interfaces with the Docker socket to spin up short-lived, deeply hardened Alpine containers.

### Hardening Parameters
*   `--read-only`: The container's root file system is mounted read-only.
*   `--tmpfs /tmp`: Only the `/tmp` directory is writable for scratch data.
*   `--cap-drop ALL`: All Linux capabilities are stripped to prevent privilege escalation.
*   `network_mode="none"`: The container is completely isolated from the internet and the host network.
*   `user="1000"`: Code executes as a low-privileged user, not root.
*   `--rm`: The container self-destructs immediately after the command yields output.

## Consequences
**Positive:** We achieve a highly reproducible, ephemeral environment where JARVIS-X can write Python scripts or run potentially harmful commands (like `rm -rf /`) without touching the user's actual filesystem or network layer.
**Negative:** It adds a dependency requirement (Docker must be installed on the host OS), and there is slight overhead in spinning up a container versus a native Popen call. Windows hosts require WSL2 integration.

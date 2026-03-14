import re
from typing import List, Tuple
from backend.security.audit import audit_logger

class CommandValidator:
    """Validates system commands against a strict allowlist and logs attempts."""
    
    # Path traversal block (pre-filter)
    PATH_TRAVERSAL = re.compile(r"\.\.\/(?:\.\.\/)+", re.IGNORECASE)
    
    # Strictly safe read-only or harmless commands
    ALLOWED_COMMANDS = [
        r"^dir\b",
        r"^ls\b",
        r"^echo\b",
        r"^pwd\b",
        r"^cd\b",
        r"^type\b",
        r"^cat\b",
        r"^ping\b",
        r"^python\s+-c\s+[\'\"]print",
        r"^whoami\b"
    ]
    
    # Commands that are inherently risky but necessary for development workflows.
    # Anything else NOT in ALLOWED or REQUIRES_APPROVAL is automatically BLOCKED.
    REQUIRES_APPROVAL_COMMANDS = [
        r"^python\s+",
        r"^pip\s+",
        r"^npm\s+",
        r"^node\s+",
        r"^git\s+",
        r"^docker\s+",
        r"^mkdir\b",
        r"^copy\b",
        r"^cp\b",
        r"^move\b",
        r"^mv\b",
        r"^touch\b",
        r"^ipconfig\b",
        r"^ifconfig\b"
    ]

    def __init__(self):
        self._allowed_compiled = [re.compile(p, re.IGNORECASE) for p in self.ALLOWED_COMMANDS]
        self._approval_compiled = [re.compile(p, re.IGNORECASE) for p in self.REQUIRES_APPROVAL_COMMANDS]

    def evaluate(self, command: str) -> Tuple[str, str]:
        """
        Evaluates if a command is safe to execute based on a strict allowlist.
        Returns a tuple of (status: str, reason: str)
        """
        # 0. Pre-filter for obvious exploits like path traversal
        if self.PATH_TRAVERSAL.search(command):
            status, reason = "BLOCKED", "Path traversal detected."
            audit_logger.log_event("SECURITY_VALIDATION", "CRITICAL", {"command": command, "status": status, "reason": reason})
            return status, reason

        # 1. Check Auto-Allowlist (read-only)
        for pattern in self._allowed_compiled:
            if pattern.search(command):
                status, reason = "ALLOWED", "Command matches auto-approved allowlist."
                audit_logger.log_event("SECURITY_VALIDATION", "INFO", {"command": command, "status": status, "reason": reason})
                return status, reason
                
        # 2. Check explicitly permitted but risky commands (requires approval)
        for pattern in self._approval_compiled:
            if pattern.search(command):
                status, reason = "REQUIRES_APPROVAL", "Command matches recognized pattern but requires explicit user approval."
                audit_logger.log_event("SECURITY_VALIDATION", "WARN", {"command": command, "status": status, "reason": reason})
                return status, reason
                
        # 3. Default Deny (Zero-Trust)
        status, reason = "BLOCKED", "Command not recognized in the explicitly allowed or approval-required lists. Denied by default."
        audit_logger.log_event("SECURITY_VALIDATION", "CRITICAL", {"command": command, "status": status, "reason": reason})
        return status, reason

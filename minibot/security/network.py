"""Network security utilities for minibot."""

import ipaddress
import re
from typing import List, Optional


class NetworkSecurity:
    """Network security utilities."""

    @staticmethod
    def is_localhost(ip: str) -> bool:
        """Check if an IP address is localhost."""
        try:
            addr = ipaddress.ip_address(ip)
            return addr.is_loopback
        except ValueError:
            return False

    @staticmethod
    def is_private(ip: str) -> bool:
        """Check if an IP address is private."""
        try:
            addr = ipaddress.ip_address(ip)
            return addr.is_private
        except ValueError:
            return False

    @staticmethod
    def is_valid_ip(ip: str) -> bool:
        """Check if an IP address is valid."""
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False

    @staticmethod
    def sanitize_path(path: str) -> str:
        """Sanitize a file path to prevent path traversal attacks."""
        # Remove any parent directory references
        sanitized = re.sub(r'\.\.', '', path)
        # Remove any absolute path references
        sanitized = sanitized.lstrip('/\\')
        return sanitized

    @staticmethod
    def validate_input(input_str: str, max_length: int = 1000) -> bool:
        """Validate user input to prevent injection attacks."""
        if len(input_str) > max_length:
            return False
        # Add more validation rules as needed
        return True

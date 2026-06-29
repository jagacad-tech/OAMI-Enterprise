"""
Custom Exceptions
"""


class OAMIError(Exception):
    """Base exception for OAMI."""


class ConfigurationError(OAMIError):
    """Configuration related error."""


class ScannerError(OAMIError):
    """Scanner related error."""


class BrokerError(OAMIError):
    """Broker related error."""
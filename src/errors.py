"""
Custom exception classes for MGL Analytics
"""


class MGL_AnalyticsException(Exception):
    """Base exception for MGL Analytics"""
    pass


class ConfigurationError(MGL_AnalyticsException):
    """Raised when configuration is invalid"""
    pass


class DatabaseError(MGL_AnalyticsException):
    """Raised when database operations fail"""
    pass


class APIError(MGL_AnalyticsException):
    """Raised when API calls fail"""
    pass


class TelegramError(MGL_AnalyticsException):
    """Raised when Telegram notification fails"""
    pass


class SignalError(MGL_AnalyticsException):
    """Raised when signal processing fails"""
    pass

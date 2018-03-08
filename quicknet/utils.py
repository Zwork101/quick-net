__all__ = ["QuickNetError", "NotRunningError", "DataOverflowError", "UnSterilizable", "BadSterilization"]


class QuickNetError(Exception):
    pass


class NotRunningError(QuickNetError):
    pass


class DataOverflowError(QuickNetError):
    pass


class UnSterilizable(QuickNetError):
    pass


class BadSterilization(QuickNetError):
    pass

__all__ = ["QuickNetError", "NotRunningError", "DataOverflowError"]


class QuickNetError(Exception):
    pass


class NotRunningError(QuickNetError):
    pass


class DataOverflowError(QuickNetError):
    pass

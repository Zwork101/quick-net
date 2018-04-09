from inspect import getfullargspec

__all__ = ["QuickNetError", "NotRunningError", "DataOverflowError",
           "UnSterilizable", "BadSterilization", "check_annotations"]


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


def check_annotations(func, args, kwargs) -> bool:
    specs = getfullargspec(func)
    for arg, name in zip(args, specs.args):
        if name in specs.annotations:
            if type(arg) != specs.annotations[name]:
                return False
    for name, val in kwargs.items():
        if name in specs:
            if type(val) != specs[name]:
                return False
    return True

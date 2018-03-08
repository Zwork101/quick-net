import builtins
from urllib.parse import quote, unquote
from types import BuiltinFunctionType, BuiltinMethodType

from quicknet.utils import UnSterilizable, BadSterilization

__all__ = ["dirty", "clean"]


def dirty(obj: any) -> str:
    if isinstance(obj, str):
        return quote("S{obj}".format(obj=obj))
    elif isinstance(obj, bool):
        return "B{v}".format(v=1 if obj else 0)
    elif isinstance(obj, int):
        return "I{obj}".format(obj=obj)
    elif isinstance(obj, float):
        return "F{obj}".format(obj=obj)
    elif obj is None:
        return 'N'
    elif isinstance(obj, list):
        if not obj:
            return "L^"
        return quote("L" + ','.join(map(dirty, obj)))
    elif isinstance(obj, tuple):
        if not obj:
            return "T^"
        return quote("T" + ','.join(map(dirty, obj)))
    elif isinstance(obj, dict):
        if not obj:
            return "D^"
        items = []
        for key, value in obj.items():
            items.append(dirty(key) + ":" + dirty(value))
        return "D" + quote(','.join(items))
    elif isinstance(obj, BuiltinFunctionType) or isinstance(obj, BuiltinMethodType):
        return quote("b{obj}".format(obj=obj.__name__))
    elif isinstance(obj, set):
        if not obj:
            return "E^"
        return quote("E" + ','.join(map(dirty, obj)))
    elif isinstance(obj, bytearray):
        return "Y" + quote(obj.hex())
    elif isinstance(obj, bytes):
        return "y" + quote(obj.hex())
    else:
        raise UnSterilizable("Can't sterilize type: {typ}".format(typ=type(obj)))


def clean(text: str):
    try:
        typ, data = text[:1], text[1:]
        if typ == 'S':
            return unquote(data)
        elif typ == 'B':
            return bool(data)
        elif typ == 'I':
            return int(data)
        elif typ == 'F':
            return float(data)
        elif typ == 'N':
            return None
        elif typ == 'L':
            data = unquote(data)
            if data == '^':
                return []
            return list(map(clean, data.split(',')))
        elif typ == 'T':
            data = unquote(data)
            if data == '^':
                return tuple()
            return tuple(map(clean, data.split(',')))
        elif typ == 'E':
            data = unquote(data)
            if data == '^':
                return set()
            return set(map(clean, data.split(',')))
        elif typ == 'D':
            data = unquote(data)
            if data == '^':
                return {}
            items = data.split(',')
            new = dict(map(lambda s: map(clean, s.split(':')), items))
            return new
        elif typ == 'b':
            return getattr(builtins, unquote(data))
        elif typ == 'Y':
            return bytearray.fromhex(data)
        elif typ == 'y':
            return bytes.fromhex(data)
        else:
            raise Exception("Unable to find type for {d}".format(d=typ))
    except Exception as e:
        raise BadSterilization(str(e))

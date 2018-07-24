import builtins
from urllib.parse import quote, unquote
from types import BuiltinFunctionType, BuiltinMethodType

from quicknet.utils import UnSterilizable, BadSterilization

__all__ = ["dirty", "clean"]


def dirty(obj: any) -> str:
    simple = {bool: "B", int: "I", float: "F"}
    byt = {bytearray: "Y", bytes: "y"}
    multi = {list: "L", tuple: "T", set: "E"}
    if type(obj) in simple:
        return "{n}{data}".format(n=simple[type(obj)], data=obj)
    elif type(obj) in byt:
        return "{n}{hex}".format(n=byt[type(obj)], hex=obj.hex())
    elif type(obj) in multi:
        if not obj:
            return multi[type(obj)] + "^"
        return quote(multi[type(obj)] + ','.join(map(dirty, obj)))
    elif type(obj) is str:
        return quote("S{obj}".format(obj=obj))
    elif obj is None:
        return 'N'
    elif type(obj) is dict:
        if not obj:
            return "D^"
        items = []
        for key, value in obj.items():
            items.append(dirty(key) + ":" + dirty(value))
        return "D" + quote(','.join(items))
    elif isinstance(obj, BuiltinFunctionType) or isinstance(obj, BuiltinMethodType):
        return quote("b{obj}".format(obj=obj.__name__))
    else:
        print(obj, type(obj))
        raise UnSterilizable("Can't sterilize type: {typ}".format(typ=type(obj)))


def clean(text: str):
    simple = {'S': unquote, 'B': bool, 'I': int, 'F': float, 'N': lambda x: None}
    byt = {'Y': bytearray, 'y': bytes}
    multi = {'L': list, 'T': tuple, 'E': set}
    try:
        typ, data = text[:1], text[1:]
        if typ in simple:
            return simple[typ](data)
        elif typ in multi:
            data = unquote(data)
            if data == '^':
                return multi[typ]()
            return multi[typ](map(clean, data.split(',')))
        elif typ in byt:
            return byt[typ].fromhex(unquote(data))
        elif typ == 'D':
            data = unquote(data)
            if data == '^':
                return {}
            items = data.split(',')
            new = dict(map(lambda s: map(clean, s.split(':')), items))
            return new
        elif typ == 'b':
            return getattr(builtins, unquote(data))
        else:
            print(typ, text)
            raise Exception("Unable to find type for {d}".format(d=typ))
    except Exception as e:
        raise BadSterilization(e)

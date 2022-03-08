import dataclasses
import enum
import json
from abc import ABC
from datetime import date
from typing import Type


class Serializer(ABC):
    registry: dict[Type, Type['Serializer']] = {}
    type = None

    def __init_subclass__(cls, **kwargs):
        cls.registry[cls.type] = cls

    @classmethod
    def dump(cls, obj):
        if dataclasses.is_dataclass(type(obj)):
            return {
                field.name: cls.dump(getattr(obj, field.name))
                for field in dataclasses.fields(obj)
            }
        for _type in type(obj).mro():
            if _type in cls.registry:
                return cls.registry[_type].dump(obj)

        return obj

    @classmethod
    def load(cls, data, _type):
        if dataclasses.is_dataclass(_type):
            return _type(**{
                field.name: cls.load(data[field.name], field.type)
                for field in dataclasses.fields(_type)
            })
        for ancestor_type in _type.mro():
            if ancestor_type in cls.registry:
                return cls.registry[ancestor_type].load(data, _type)
        if hasattr(_type, '__origin__'):
            for ancestor_type in _type.__origin__.mro():
                if ancestor_type in cls.registry:
                    return cls.registry[ancestor_type].load(data, _type)

        return data


def iterable_serializer(t: Type):
    class IterableSerializer(Serializer):
        type = t

        @classmethod
        def dump(cls, obj):
            return [Serializer.dump(x) for x in obj]

        @classmethod
        def load(cls, data, _type):
            item_type = None
            if hasattr(_type, '__args__'):
                item_type = _type.__args__[0]
            return t(Serializer.load(x, item_type) for x in data)

    return IterableSerializer


iterable_serializer(list)
iterable_serializer(tuple)


class DateSerializer(Serializer):
    type = date

    @classmethod
    def dump(cls, obj: date):
        return obj.isoformat()

    @classmethod
    def load(cls, data, _type):
        return date.fromisoformat(data)


class EnumSerializer(Serializer):
    type = enum.Enum

    @classmethod
    def dump(cls, obj: enum.Enum):
        return obj.value

    @classmethod
    def load(cls, data, _type):
        return _type(data)


dump_j = Serializer.dump
load_j = Serializer.load


def dumps(obj):
    return json.dumps(dump_j(obj))


def loads(data_string, _type):
    return load_j(json.loads(data_string), _type)


def dump(obj, file):
    file.write(dumps(obj))


def load(_type, file):
    data = file.read()
    try:
        return loads(data, _type)
    except json.JSONDecodeError:
        raise
    except Exception:
        raise json.JSONDecodeError('Cannot be interpreted as the correct type', data, 0)

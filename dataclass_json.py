import dataclasses
import collections
import enum
import json
import typing
from datetime import date
from typing import Callable, Type
from abc import ABC, abstractmethod


class Serializer(ABC):
    registry: dict[Type, Type['Serializer']] = {}
    type = None

    def __init_subclass__(cls, **kwargs):
        cls.registry[cls.type] = cls

    @classmethod
    def dumpj(cls, obj):
        if dataclasses.is_dataclass(type(obj)):
            return {
                field.name: cls.dumpj(getattr(obj, field.name))
                for field in dataclasses.fields(obj)
            }
        for _type in type(obj).mro():
            if _type in cls.registry:
                return cls.registry[_type].dumpj(obj)

        return obj

    @classmethod
    def loadj(cls, data, _type):
        if dataclasses.is_dataclass(_type):
            return _type(**{
                field.name: cls.loadj(data[field.name], field.type)
                for field in dataclasses.fields(_type)
            })
        for ancestor_type in _type.mro():
            if ancestor_type in cls.registry:
                return cls.registry[ancestor_type].loadj(data, _type)
        if hasattr(_type, '__origin__'):
            for ancestor_type in _type.__origin__.mro():
                if ancestor_type in cls.registry:
                    return cls.registry[ancestor_type].loadj(data, _type)

        return data


def iterable_serializer(t: Type):
    class IterableSerializer(Serializer):
        type = t

        @classmethod
        def dumpj(cls, obj):
            return [Serializer.dumpj(x) for x in obj]

        @classmethod
        def loadj(cls, data, _type):
            item_type = None
            if hasattr(_type, '__args__'):
                item_type = _type.__args__[0]
            return t(Serializer.loadj(x, item_type) for x in data)

    return IterableSerializer


iterable_serializer(list)
iterable_serializer(tuple)


class DateSerializer(Serializer):
    type = date

    @classmethod
    def dumpj(cls, obj: date):
        return obj.isoformat()

    @classmethod
    def loadj(cls, data, _type):
        return date.fromisoformat(data)


class EnumSerializer(Serializer):
    type = enum.Enum

    @classmethod
    def dumpj(cls, obj: enum.Enum):
        return obj.value

    @classmethod
    def loadj(cls, data, _type):
        return _type(data)


dumpj = Serializer.dumpj
loadj = Serializer.loadj


def dumps(obj):
    return json.dumps(dumpj(obj))


def loads(data_string, _type):
    return loadj(json.loads(data_string), _type)


def dump(obj, file):
    file.write(dumps(obj))


def load(_type, file):
    return loads(file.read(), _type)

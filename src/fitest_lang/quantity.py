import datetime
import sys

import pint

from .baseobject import FitestBaseObject, FitestObject
from .expression import Value, Variable

units = pint.UnitRegistry()
Quantity = units.Quantity


class PhysicalQuantityBase(FitestBaseObject, FitestObject):
    @staticmethod
    def textx_type_class(textx_type):
        t = str(textx_type)
        if not 'Value' in t and not 'Variable' in t:
            return getattr(sys.modules[__name__], t[t.find(".") + 1: t.find(" ")])
        elif 'Value' in t:
            return Value
        elif 'Variable' in t:
            return Variable


class PhysicalQuantity(PhysicalQuantityBase):
    def __init__(self, magnitude, units):
        self.magnitude = magnitude
        self.units = units

    def eval_exprs(self, env={}):
        try:
            return self.__class__(self.magnitude.eval_exprs(env=env), self.units)
        except:
            return self.__class__(self.magnitude, self.units)

    def to_quantity(self, env={}):
        if not type(self.magnitude) in [int, float]:
            return Quantity(self.magnitude.eval_exprs(env=env), self.units)
        else:
            return Quantity(self.magnitude, self.units)

    def to_str(self, env={}, eval_exprs=False):
        try:
            return (
                self.magnitude.to_str(env=env, eval_exprs=eval_exprs) + " " + str(self.units)
            )
        except:
            return str(self.magnitude) + " " + str(self.units)

    def to_ir(self):
        return {
            self.cls_name(): {"magnitude": self.magnitude.to_ir(), "units": self.units}
        }

    def __str__(self):
        return self.to_str()

    def __repr__(self):
        return (
            "<"
            + self.cls_name()
            + "("
            + ",".join([repr(self.magnitude), str(self.units)])
            + ")>"
        )

    def __add__(self, other):
        q = Quantity(self.magnitude, self.units) + Quantity(
            other.magnitude, other.units
        )
        return self.__class__(q.magnitude, q.units)

    def __radd__(self, other):
        q = Quantity(self.magnitude, self.units) + Quantity(
            other.magnitude, other.units
        )
        return self.__class__(q.magnitude, q.units)

    def __mul__(self, other, env={}):
        if not type(self.magnitude) in [int, float]:
            magnitude = self.magnitude.eval_exprs(env=env)
        else:
            magnitude = self.magnitude
        if type(other) == Quantity or type(other) == self.__class__:
            q = Quantity(magnitude, self.units) * Quantity(other.magnitude, other.units)
        elif type(other) in [int, float]:
            q = Quantity(magnitude, self.units) * other
        if not q.dimensionless:
            return self.__class__(q.magnitude, q.units)
        else:
            return q.magnitude

    def __truediv__(self, other, env={}):
        if not type(self.magnitude) in [int, float]:
            magnitude = self.magnitude.eval_exprs(env=env)
        else:
            magnitude = self.magnitude
        if type(other) == Quantity or type(other) == self.__class__:
            q = Quantity(magnitude, self.units) / Quantity(other.magnitude, other.units)
        elif type(other) in [int, float]:
            q = Quantity(magnitude, self.units) / other
        if not q.dimensionless:
            return self.__class__(q.magnitude, q.units)
        else:
            return q.magnitude

    @classmethod
    def from_ir(cls, ir):
        return cls(
            magnitude=cls.textx_type_class(ir.magnitude).from_ir(ir.magnitude),
            units=ir.units,
        )

    @classmethod
    def from_quantity(cls, q, num_decimals=1): 
        return cls(round(q.magnitude, num_decimals), q.units)


class Length(PhysicalQuantity):
    pass


class Weight(PhysicalQuantity):
    pass


class Work(PhysicalQuantity):
    pass


class Repetition(PhysicalQuantity):
    def __init__(self, magnitude=None, units=None):
        self.magnitude = magnitude
        self.units = units
        self.is_variable = not (self.magnitude and self.units)

    def get_num_rds(self):
        return self.magnitude.eval_exprs()

    def to_list(self):
        return list(range(self.magnitude.eval_exprs()))

    def to_str(self, env={}, eval_exprs=False):
        if not self.is_variable:
            return (
                self.magnitude.to_str(env=env, eval_exprs=eval_exprs) + " " + self.units
            )
        else:
            return "R"

    def __repr__(self):
        if not self.is_variable:
            return (
                "<"
                + self.cls_name()
                + "("
                + ",".join([repr(self.magnitude), str(self.units)])
                + ")>"
            )
        else:
            return "<Repetition(R)>"


class Time(PhysicalQuantity):
    def __init__(self, magnitude=None, units=None):
        self.magnitude = magnitude
        self.units = units
        self.is_variable = not (self.magnitude and self.units)

    def to_str(self, env={}, eval_exprs=False):
        if not self.is_variable:
            return (
                self.magnitude.to_str(env=env, eval_exprs=eval_exprs) + " " + self.units
            )
        else:
            return "T"

    def __repr__(self):
        if not self.is_variable:
            return (
                "<"
                + self.cls_name()
                + "("
                + ",".join([repr(self.magnitude), str(self.units)])
                + ")>"
            )
        else:
            return "<Time(T)>"

    def __add__(self, other):
        if not self.is_variable and not other.is_variable:
            q = Quantity(self.magnitude, self.units) + Quantity(
                other.magnitude, other.units
            )
            return self.__class__(q.magnitude, q.units)
        else:
            return self.__class__()

    def __radd__(self, other):
        if not self.is_variable and not other.is_variable:
            q = Quantity(self.magnitude, self.units) + Quantity(
                other.magnitude, other.units
            )
            return self.__class__(q.magnitude, q.units)
        else:
            return self.__class__()

    def to_dict(self, env={}):
        if not type(self.magnitude) == int:
            m = self.magnitude.eval_exprs(env=env)
        else:
            m = self.magnitude
        # acta_grammar.Time => {'hours': hh, 'minutes': mm, 'seconds': ss}
        if self.units in ["hr", "hour"]:
            return {"hours": m, "minutes": 0, "seconds": 0}
        elif self.units in ["min", "minute"]:
            return {"hours": 0, "minutes": m, "seconds": 0}
        elif self.units in ["s", "sec"]:
            return {"hours": 0, "minutes": 0, "seconds": m}

    def to_timedelta(self):
        return datetime.timedelta(**self.to_dict())

    @staticmethod
    def time_dict_to_secs(time_dict):
        return (
            time_dict["hours"] * 3600 + time_dict["minutes"] * 60 + time_dict["seconds"]
        )

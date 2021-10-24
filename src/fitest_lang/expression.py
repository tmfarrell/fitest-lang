import sys

from .baseobject import FitestBaseObject, FitestObject


class ExpressionBase(FitestBaseObject, FitestObject):
    @staticmethod
    def textx_type_class(textx_type):
        t = str(textx_type)
        return getattr(sys.modules[__name__], t[t.find(".") + 1: t.find(" ")])


class Expression(ExpressionBase):
    def __init__(self, expr):
        self.expr = expr

    def eval_exprs(self, env={}):
        return self.expr.eval_exprs(env=env)

    def to_str(self, env=None, eval_exprs=False):
        return self.expr.to_str(env=env, eval_exprs=eval_exprs)

    def to_ir(self):
        return {"Expression": self.expr.to_ir()}

    def __str__(self):
        return self.expr.to_str()

    def __repr__(self):
        return "<" + self.cls_name() + "(" + self.expr.__repr__() + ")>"

    @classmethod
    def from_ir(cls, ir):
        return cls(Sum.from_ir(ir.expr))


class Sum(ExpressionBase):
    def __init__(self, left, ops, right):
        self.left = left
        self.ops = ops
        self.right = right

    def eval_exprs(self, env={}):
        return eval(self.to_str(env=env, eval_exprs=True))

    def to_str(self, env=None, eval_exprs=False):
        s = self.left.to_str(env=env, eval_exprs=eval_exprs)
        if self.right:
            products = map(
                lambda r: r.to_str(env=env, eval_exprs=eval_exprs), self.right
            )
            s = (
                    s
                    + " "
                    + "".join([" ".join(op_prod) for op_prod in zip(self.ops, products)])
            )
            if eval_exprs:
                s = str(int(eval(s)))
        return s

    def to_ir(self):
        return {
            "Sum": {
                "left": self.left.to_ir(),
                "ops": self.ops,
                "right": [r.to_ir() for r in self.right],
            }
        }

    def __str__(self):
        return self.to_str()

    def __repr__(self):
        s = str(self.left)
        if self.right:
            products = map(repr, self.right)
            s = (
                    s
                    + " "
                    + "".join([" ".join(op_prod) for op_prod in zip(self.ops, products)])
            )
        return s

    @classmethod
    def from_ir(cls, ir):
        return cls(
            left=Product.from_ir(ir.left),
            ops=ir.op,
            right=[Product.from_ir(r) for r in ir.right],
        )


class Product(ExpressionBase):
    def __init__(self, left, ops, right):
        self.left = left
        self.ops = ops
        self.right = right

    def to_str(self, env=None, eval_exprs=False):
        s = self.left.to_str(env=env, eval_exprs=eval_exprs)
        if self.right:
            vals = map(lambda r: r.to_str(env=env, eval_exprs=eval_exprs), self.right)
            s = s + " " + "".join([" ".join(op_val) for op_val in zip(self.ops, vals)])
            if eval_exprs:
                s = str(int(eval(s)))
        return s

    def eval_exprs(self, env={}):
        return eval(self.to_str(env=env, eval_exprs=True))

    def to_ir(self):
        return {
            "Product": {
                "left": self.left.to_ir(),
                "ops": self.ops,
                "right": [r.to_ir() for r in self.right],
            }
        }

    def __str__(self):
        return self.to_str()

    def __repr__(self):
        s = str(self.left)
        if self.right:
            vals = map(repr, self.right)
            s = (
                    s
                    + " "
                    + "".join([" ".join(op_prod) for op_prod in zip(self.ops, vals)])
            )
        return s

    @classmethod
    def from_ir(cls, ir):
        return cls(
            left=Value.from_ir(ir.left),
            ops=ir.op,
            right=[Value.from_ir(r) for r in ir.right],
        )


class Value(ExpressionBase):
    def __init__(self, val):
        self.val = val

    def to_str(self, env=None, eval_exprs=False):
        if type(self.val) == Expression:
            return self.val.to_str(env=env, eval_exprs=eval_exprs)
        elif eval_exprs and env and type(self.val) == str:
            return str(env[self.val])
        else:
            return str(self.val)

    def eval_exprs(self, env={}):
        if type(self.val) in [int, float]:
            return self.val
        elif type(self.val) == Expression:
            return self.val.eval_exprs(env=env)
        else:
            return env[self.val]

    def to_ir(self):
        if type(self.val) in [int, float, str]:
            return {"Value": self.val}
        else:
            return {"Value": self.val.to_ir()}

    def __str__(self):
        return self.val.__str__()

    def __repr__(self):
        if not type(self.val) == str:
            return self.val.__repr__()
        else:
            return self.val

    @classmethod
    def from_ir(cls, ir):
        if type(ir.val) in [int, float]:
            return cls(val=ir.val)
        elif ir.type:
            t = str(ir.type)
            return cls(val=t[t.find(":") + 1: -1])
        else:
            return cls(val=Expression.from_ir(ir.val))


class Variable(ExpressionBase):
    def __init__(self, name, ints):
        self.name = name
        self.ints = ints

    def get_num_rds(self):
        return len(self.ints)

    def to_env(self):
        return {self.name: self.ints}

    def to_list(self):
        return self.ints

    def to_ir(self):
        return {"Variable": {"name": self.name, "ints": self.ints}}

    def __str__(self):
        return self.name + " in " + " ".join(map(str, self.ints))

    def __repr__(self):
        return "<" + self.cls_name() + "(" + self.name + "," + str(self.ints) + ")>"

    @classmethod
    def from_ir(cls, ir):
        return cls(name=ir.name, ints=ir.ints)

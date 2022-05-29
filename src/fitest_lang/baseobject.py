from copy import deepcopy, copy
import json


class FitestBaseObject(object):
    @classmethod
    def cls_name(cls):
        cl_name = str(cls)
        return cl_name[cl_name.find(".") + 1 : -2]

    def __ne__(self, other):
        if isinstance(other, self.__class__):
            return not self.__eq__(other)
        return False

    def __hash__(self):
        return hash(tuple(sorted(self.__dict__.items())))

    def _copy(self):
        return copy(self)

    def _deepcopy(self):
        return deepcopy(self)


class FitestObject:
    @staticmethod
    def textx_type_class(textx_type):
        raise NotImplementedError

    @classmethod
    def from_ir(cls, args):
        raise NotImplementedError

    @classmethod
    def to_ir(cls, args):
        raise NotImplementedError

    @classmethod
    def ir_to_str(cls, ir):
        return cls.from_ir(ir).__str__()

    @classmethod
    def ir_to_timer_objs(cls, ir, env={}, eval_exprs=False):
        return cls.from_ir(ir).to_timer_objs(env=env, eval_exprs=eval_exprs)

    def to_json(self, top=True):
        return json.dumps(self.to_ir(top), indent=1)

import datetime
import itertools as it
import sys
from types import FunctionType

import numpy as np
import pandas as pd

from .baseobject import FitestBaseObject, FitestObject
from .expression import Variable, Value
from .quantity import Repetition, Time
from .movement import MovementSeq, Rest


class ProgramBase(FitestBaseObject, FitestObject):
    @staticmethod
    def textx_type_class(textx_type):
        t = str(textx_type)
        if not 'Value' in t and not 'Variable' in t:
            t = t[t.find(".") + 1: t.find(" ")]
            if t == 'MovementSeq':
                return MovementSeq
            return getattr(sys.modules[__name__], t)
        elif 'Value' in t:
            return Value
        elif 'Variable' in t:
            return Variable

class Program(ProgramBase):
    def __init__(self, program, name=None, time=None, reps=None):
        self.program = program
        self.name = name
        self.time = time
        self.reps = reps

    def set_time(self, t):
        self.time = t

    def get_time(self):
        return self.program.get_time()

    def set_reps(self, r):
        self.reps = r

    def get_reps(self):
        return self.program.get_reps()

    def get_work(self, athlete):
        return self.program.get_work(athlete)

    def get_power(self, athlete, score):
        return self.program.get_power(athlete, score)

    def describe(self, by="mvmt_category"):
        return self.program.describe(by=by)

    def to_timer_objs(self, env=None, eval_exprs=False):
        return self.program.to_timer_objs(env=env, eval_exprs=eval_exprs)

    def to_ir(self, top=False, env=None, eval_exprs=False):
        ir = {"Program": self.program.to_ir()}
        if top:
            return {
                "type": "Program",
                "ir": ir,
                "timer_objs": [
                    (t.seconds, s)
                    for t, s in self.to_timer_objs(env=env, eval_exprs=eval_exprs)
                ],
                "str": self.__str__(),
            }
        else:
            return ir

    def __str__(self):
        return self.program.__str__()

    def __repr__(self):
        if not self.name:
            return "<" + self.cls_name() + "(" + self.program.__repr__() + ")>"
        else:
            return (
                "<"
                + self.cls_name()
                + "("
                + self.name
                + ","
                + self.program.__repr__()
                + ")>"
            )

    @classmethod
    def from_ir(cls, ir):
        return cls.textx_type_class(ir).from_ir(ir)


## PROGRAM TYPES ##
class TaskPriority(ProgramBase):
    def __init__(self, reps, seq, rest=None):
        self.reps = reps
        self.seq = seq
        self.rest = rest

    def get_time(self):
        ts = []
        for (reps, seq, rest) in self.to_list():
            for j in range(reps.get_num_rds()):
                if type(reps) == Variable:
                    env = {reps.name: reps.ints[j]}
                else:
                    env = {}
                ts = ts + [seq.get_time(env=env)]
            if not rest is None:
                ts = ts + [rest.get_time(env=env)]
        return ts

    def get_reps(self):
        rs = []
        for (reps, seq, _) in self.to_list():
            for j in range(reps.get_num_rds()):
                if type(reps) == Variable:
                    env = {reps.name: reps.ints[j]}
                else:
                    env = {}
                rs = rs + [seq.get_reps(env=env)]
        return rs

    def get_num_rds(self):
        return np.shape(self.get_rds())

    def get_rds(self):
        return [r.to_list() for r in self.reps]

    def get_work(self, athlete, by_round=False, work_units="cal"):
        rs = []
        for (reps, seq, _) in self.to_list():
            for j in range(reps.get_num_rds()):
                if type(reps) == Variable:
                    env = {reps.name: reps.ints[j]}
                else:
                    env = {}
                rs += [seq.get_work(athlete, env=env)]

        if any([type(r) == FunctionType for r in rs]):

            def work_fcn(scores):
                assert len(scores) == len(
                    rs
                ), "scores must correspond one-to-one to mvmt_seqs"
                results = [r(score).to(work_units) for score, r in zip(scores, rs)]
                if by_round:
                    return results
                else:
                    return sum(results)

            return work_fcn
        else:
            if by_round:
                return [r.to(work_units) for r in rs]
            else:
                return sum(rs).to(work_units)

    def describe(self, by="mvmt_category", verbose=False):
        rs = []
        for (reps, seq, rest) in self.to_list():
            for j in range(reps.get_num_rds()):
                if type(reps) == Variable:
                    env = {reps.name: reps.ints[j]}
                else:
                    env = {}
                rs += [seq.describe(by=by, env=env)]
                if rest:
                    if seq.time_priority:
                        rs += [{"rest": 1.0}]
                    else:
                        rs += [{"rest": 1.0}]
        if not "work" in rs[0].keys():
            rs = pd.DataFrame(rs)
        else:
            rs = pd.DataFrame(
                [
                    dict(**rs[i]["work"], **{"rest": rs[i]["rest"]})
                    for i in range(len(rs))
                ]
            )
        if "rest" in rs.columns:
            rs["rest"] = rs["rest"].fillna(0.0)
        rs = rs.mean().round(3).to_dict()
        if sum(rs.values()) > 1.0:
            return dict(
                **{"work": {k: v for k, v in rs.items() if k != "rest"}},
                **{"rest": rs["rest"]}
            )
        else:
            return rs

    def to_list(self):
        return list(it.zip_longest(self.reps, self.seq, self.rest))

    def to_timer_objs(self, env=None, eval_exprs=False):
        times, seq_strs = [], []
        for i in range(len(self.reps)):
            reps_type = type(self.reps[i])
            if reps_type == Repetition:
                num_rds = self.reps[i].magnitude
                for j in range(num_rds):
                    ts, ss = zip(*self.seq[i].to_timer_objs())
                    ss = [
                        ("round " + str(j + 1) + " of " + str(num_rds) + ":\n" + s)
                        for s in ss
                    ]
                    times = times + list(ts)
                    seq_strs = seq_strs + ss
            elif reps_type == Variable:
                var_name = self.reps[i].name
                int_list = self.reps[i].ints
                num_rds = len(int_list)
                for j in range(num_rds):
                    ts, ss = zip(
                        *self.seq[i].to_timer_objs(
                            env={var_name: int_list[j]}, eval_exprs=True
                        )
                    )
                    ss = [
                        ("round " + str(j + 1) + " of " + str(num_rds) + ":\n" + s)
                        for s in ss
                    ]
                    times = times + list(ts)
                    seq_strs = seq_strs + ss
        return list(zip(times, seq_strs))

    def to_ir(self, top=False, env=None, eval_exprs=False):
        ir = {
            "TaskPriority": {
                "reps": [r.to_ir() for r in self.reps],
                "seq": [s.to_ir() for s in self.seq],
                "rest": [r.to_ir() for r in self.rest],
            }
        }
        if top:
            return {
                "type": "TaskPriority",
                "ir": ir,
                "timer_objs": [
                    (t.seconds, s)
                    for t, s in self.to_timer_objs(env=env, eval_exprs=eval_exprs)
                ],
                "str": self.__str__(),
            }
        else:
            return ir

    def __str__(self):
        s = ""
        num_in_seq = len(self.reps)
        for i in range(num_in_seq):
            reps_type = type(self.reps[i])
            if reps_type == Variable:
                s = s + "for "
            s = s + self.reps[i].__str__() + ":\n"
            s = s + self.seq[i].__str__()
        return s

    def __repr__(self):
        return (
            "<" + self.cls_name() + "([" + ",".join(map(repr, self.to_list())) + "])>"
        )

    @classmethod
    def from_ir(cls, ir):
        return cls(
            reps=[cls.textx_type_class(r).from_ir(r) for r in ir.reps],
            seq=[cls.textx_type_class(s).from_ir(s) for s in ir.seq],
            rest=[cls.textx_type_class(r).from_ir(r) for r in ir.rest],
        )


class TimePriority(ProgramBase):
    def __init__(self, time, seq, rest):
        self.time = time
        self.seq = seq
        self.rest = rest

    def get_time(self):
        return [
            x
            for x in it.chain(self.time, [r.get_time() for r in self.rest])
            if not x is None
        ]

    def get_reps(self):
        return [s.get_reps() for s in self.seq]

    def get_work(self, athlete, by_round=False, work_units="cal"):
        def work_fcn(scores):
            assert len(scores) == len(
                self.seq
            ), "scores must correspond one-to-one with mvmt seqs"
            rs = [
                (score * seq.get_work(athlete)).to(work_units)
                for score, seq in zip(scores, self.seq)
            ]
            if by_round:
                return rs
            else:
                return sum(rs)

        return work_fcn

    def describe(self, by="mvmt_category"):
        rs = []
        for (time, seq, rest) in self.to_list():
            rs = rs + [seq.describe(by=by)]
            if rest:
                if seq.time_priority:
                    rs = rs + [{"rest": 1.0}]
                else:
                    rs = rs + [{"rest": 1.0}]
        if not "work" in rs[0].keys():
            rs = pd.DataFrame(rs)
        else:
            rs = pd.DataFrame(
                [
                    dict(**rs[i]["work"], **{"rest": rs[i]["rest"]})
                    for i in range(len(rs))
                ]
            )
        if "rest" in rs.columns:
            rs["rest"] = rs["rest"].fillna(0.0)
        rs = rs.mean().round(3).to_dict()
        if sum(rs.values()) > 1.0:
            return dict(
                **{"work": {k: v for k, v in rs.items() if k != "rest"}},
                **{"rest": rs["rest"]}
            )
        else:
            return rs
        # return(rs.mean().round(3).to_dict())
        # return(pd.DataFrame(rs).fillna(0.0).mean().to_dict())

    def to_list(self):
        return list(it.zip_longest(self.time, self.seq, self.rest))

    def to_ir(self, top=False):
        ir = {
            "TimePriority": {
                "time": [t.to_ir() for t in self.time],
                "seq": [s.to_ir() for s in self.seq],
                "rest": [r.to_ir() for r in self.rest],
            }
        }
        if top:
            return {
                "type": "TimePriority",
                "ir": ir,
                "timer_objs": [(t.seconds, s) for t, s in self.to_timer_objs()],
                "str": self.__str__(),
            }
        else:
            return ir

    def __str__(self):
        s = ""
        num_in_seq = len(self.time)
        for i in range(num_in_seq):
            s = s + "AMRAP " + self.time[i].__str__() + ":\n"
            s = s + self.seq[i].__str__()
        return s

    def __repr__(self):
        return (
            "<" + self.cls_name() + "([" + ",".join(map(repr, self.to_list())) + "])>"
        )

    @classmethod
    def from_ir(cls, ir):
        return cls(
            time=[cls.textx_type_class(t).from_ir(t) for t in ir.time],
            seq=[cls.textx_type_class(s).from_ir(s) for s in ir.seq],
            rest=[cls.textx_type_class(r).from_ir(r) for r in ir.rest],
        )


class TimeCappedTask(FitestBaseObject, FitestObject):
    def __init__(self, time, seq, rest):
        self.time = time
        self.seq = seq
        self.rest = rest

    def get_time(self, env={}):
        return [
            x
            for x in it.chain(
                [t.eval_exprs(env=env) for t in self.time],
                [r.get_time(env=env) for r in self.rest],
            )
            if not x is None
        ]

    def get_reps(self, env={}):
        return [s.get_reps(env=env) for s in self.seq]

    def get_work(self, athlete, env={}, by_round=False, work_units="cal"):
        rs = [s.get_work(athlete, env=env).to(work_units) for s in self.seq]
        if by_round:
            return rs
        else:
            return sum(rs)

    def describe(self, by="mvmt_category", env={}):
        rs = []
        for (time, seq, rest) in self.to_list():
            rs = rs + [seq.describe(by=by, env=env)]
            if rest:
                if seq.time_priority:
                    rs = rs + [{"rest": 1.0}]
                else:
                    rs = rs + [{"rest": 1.0}]
        rs = pd.DataFrame(rs)
        if "rest" in rs.columns:
            rs["rest"] = rs["rest"].fillna(0.0)
        rs = rs.mean().round(3).to_dict()
        if sum(rs.values()) > 1.0:
            return dict(
                **{"work": {k: v for k, v in rs.items() if k != "rest"}},
                **{"rest": rs["rest"]}
            )
        else:
            return rs
        # return(rs.mean().round(3).to_dict())
        # return(pd.DataFrame(rs).fillna(0.0).mean().to_dict())

    def to_list(self):
        return list(it.zip_longest(self.time, self.seq, self.rest))

    def to_ir(self, top=False):
        ir = {
            "TimeCappedTask": {
                "time": [t.to_ir() for t in self.time],
                "seq": [s.to_ir() for s in self.seq],
                "rest": [r.to_ir() for r in self.rest],
            }
        }
        if top:
            return {
                "type": "TimeCappedTask",
                "ir": ir,
                "timer_objs": [(t.seconds, s) for t, s in self.to_timer_objs()],
                "str": self.__str__(),
            }
        else:
            return ir

    def __str__(self):
        s = ""
        num_in_seq = len(self.time)
        for i in range(num_in_seq):
            s = s + "in " + self.time[i].__str__() + ":\n"
            s = s + self.seq[i].__str__()
        return s

    def __repr__(self):
        return (
            "<"
            + self.cls_name()
            + "("
            + ",".join(map(repr, filter(lambda xs: xs != [], [self.time, self.seq])))
            + ")>"
        )

    @classmethod
    def from_ir(cls, ir):
        return cls(
            time=[cls.textx_type_class(t).from_ir(t) for t in ir.time],
            seq=[cls.textx_type_class(s).from_ir(s) for s in ir.seq],
            rest=[cls.textx_type_class(r).from_ir(r) for r in ir.rest],
        )


class TimePriorityBase(ProgramBase):
    def __init__(self, time, seq, rest=None):
        self.time = time
        self.seq = seq
        self.rest = rest

    def get_time(self, env={}):
        return [
            x
            for x in it.chain(
                [t.eval_exprs(env=env) for t in self.time],
                [r.get_time(env=env) for r in self.rest],
            )
            if not x is None
        ]

    def get_reps(self, env={}):
        return [s.get_reps(env=env) for s in self.seq]

    def get_work(self, athlete, env={}, by_round=False, work_units="cal"):
        def work_fcn(scores):
            assert len(scores) == len(
                self.seq
            ), "scores must correspond one-to-one with mvmt seqs"
            work = []
            for score, seq in zip(scores, self.seq):
                w = seq.get_work(athlete, env=env)
                if type(w) == FunctionType:
                    work += [score * w(self.time / score).to(work_units)]
                else:
                    work += [w.to(work_units)]
            rs = [
                (score * seq.get_work(athlete, env=env)).to(work_units)
                for score, seq in zip(scores, self.seq)
            ]
            if by_round:
                return rs
            else:
                return sum(rs)

        return work_fcn

    def describe(self, by="mvmt_category", env={}):
        rs = []
        for (time, seq, rest) in self.to_list():
            rs += [seq.describe(by=by, env=env)]
            if rest:
                if seq.time_priority:
                    rs += [{"rest": 1.0}]
                else:
                    rs += [{"rest": 1.0}]
        rs = pd.DataFrame(rs)
        if "rest" in rs.columns:
            rs["rest"] = rs["rest"].fillna(0.0)
        rs = rs.mean().round(3).to_dict()
        if sum(rs.values()) > 1.0:
            return dict(
                **{"work": {k: v for k, v in rs.items() if k != "rest"}},
                **{"rest": rs["rest"]}
            )
        else:
            return rs
        # return(rs.mean().round(3).to_dict())
        # return(pd.DataFrame(rs).fillna(0.0).mean().to_dict())

    def to_list(self):
        return list(it.zip_longest(self.time, self.seq, self.rest))

    def to_timer_objs(self, env=None, eval_exprs=False):
        times, seq_strs = [], []
        num_in_seq = len(self.time)
        for i in range(num_in_seq):
            # add time and mvmt_seq
            times += [datetime.timedelta(**self.time[i].to_dict())]
            s = "AMRAP " + self.time[i].__str__() + ":\n"
            s = s + self.seq[i].to_str(
                include_rest=False, env=env, eval_exprs=eval_exprs
            )
            seq_strs += [s]
            # add rest
            if self.seq[i].rest:
                times += [
                    datetime.timedelta(**self.seq[i].rest[0].magnitude.to_dict())
                ]
                seq_strs += ["rest"]
        return list(zip(times, seq_strs))

    def to_ir(self, top=False):
        ir = {
            "TimePriorityBase": {
                "time": [t.to_ir() for t in self.time],
                "seq": [s.to_ir() for s in self.seq],
                "rest": [r.to_ir() for r in self.rest],
            }
        }
        if top:
            return {
                "type": "TimePriorityBase",
                "ir": ir,
                "timer_objs": [(t.seconds, s) for t, s in self.to_timer_objs()],
                "str": self.__str__(),
            }
        else:
            return ir

    def __str__(self):
        s = ""
        num_in_seq = len(self.time)
        for i in range(num_in_seq):
            s += ("AMRAP " + self.time[i].__str__() + ":\n"
                  + self.seq[i].__str__() + "\n")
        return s

    def __repr__(self):
        return (
            "<" + self.cls_name() + "([" + ",".join(map(repr, self.to_list())) + "])>"
        )

    @classmethod
    def from_ir(cls, ir):
        return cls(
            time=[cls.textx_type_class(t).from_ir(t) for t in ir.time],
            seq=[cls.textx_type_class(s).from_ir(s) for s in ir.seq],
            rest=[cls.textx_type_class(r).from_ir(r) for r in ir.rest],
        )


class TaskPriorityBase(ProgramBase):
    def __init__(self, reps, seq, rest=None):
        self.reps = reps
        self.seq = seq
        self.rest = rest

    def get_time(self, by_mvmt=False, env={}):
        ts = []
        for (reps, seq, rest) in self.to_list():
            for j in range(reps.get_num_rds):
                env = {reps.name: reps.ints[j]} if type(reps) == Variable else {}
                ts += [seq.get_time(env=env, by_mvmt=by_mvmt)]
            if not rest is None:
                ts += [rest.get_time(env=env)]
        return ts

    def get_reps(self):
        rs = []
        for (reps, seq, _) in self.to_list():
            for j in range(reps.get_num_rds()):
                if type(reps) == Variable:
                    env = {reps.name: reps.ints[j]}
                else:
                    env = {}
                rs += [seq.get_reps(env=env)]
        return rs

    def get_num_rds(self):
        return np.shape(self.get_rds())

    def get_rds(self):
        return [r.to_list() for r in self.reps]

    def get_work(self, athlete, by_round=False, work_units="cal"):
        ss = []
        for (reps, seq, _) in self.to_list():
            for j in range(reps.get_num_rds()):
                if type(reps) == Variable:
                    env = {reps.name: reps.ints[j]}
                else:
                    env = {}
                ss += [seq.get_work(athlete, env=env)]
        if any([type(r) == FunctionType for r in ss]):

            def work_fcn(scores):
                assert len(scores) == len(
                    ss
                ), "scores must correspond one-to-one to mvmt_seqs (%d, %d)" % (
                    len(scores),
                    len(ss),
                )
                rs = [r(score).to(work_units) for score, r in zip(scores, ss)]
                if by_round:
                    return rs
                else:
                    return sum(rs)

            return work_fcn
        else:
            if by_round:
                return [r.to(work_units) for r in ss]
            else:
                return sum(ss).to(work_units)

    def describe(self, by="mvmt_category"):
        rs = []
        for (reps, seq, rest) in self.to_list():
            for j in range(reps.get_num_rds()):
                if type(reps) == Variable:
                    env = {reps.name: reps.ints[j]}
                else:
                    env = {}
                rs += [seq.describe(by=by, env=env)]
                if rest:
                    if seq.time_priority:
                        rs += [{"rest": 1.0}]
                    else:
                        rs += [{"rest": 1.0}]
        rs = pd.DataFrame(rs)
        if "rest" in rs.columns:
            rs["rest"] = rs["rest"].fillna(0.0)
        rs = rs.mean().round(3).to_dict()
        if sum(rs.values()) > 1.0:
            return dict(
                **{"work": {k: v for k, v in rs.items() if k != "rest"}},
                **{"rest": rs["rest"]}
            )
        else:
            return rs

    def to_list(self):
        return list(it.zip_longest(self.reps, self.seq, self.rest))

    def to_str(self, by_round=False, eval_exprs=False):
        s = ""
        for rep, seq, rest in self.to_list():
            reps_type = type(rep)
            if not by_round:
                if reps_type == Variable:
                    s += "for "
                s += rep.__str__() + ":\n" + seq.__str__() + "\n"
                if rest:
                    s += rest.__str__() + "\n\n"
            else:
                if reps_type == Repetition:
                    for j in range(rep.magnitude):
                        s += "round " + str(j + 1) + ":\n" + seq.__str__() + "\n"
                    if rest:
                        s += rest.__str__() + "\n\n"
                elif reps_type == Variable:
                    var_name = rep.name
                    int_list = rep.ints
                    for j in range(len(int_list)):
                        s += (
                                "round " + str(j + 1) + ":\n"
                                + seq.to_str(env={var_name: int_list[j]}, eval_exprs=eval_exprs)
                                + "\n"
                        )
                    if rest:
                        s += rest.__str__() + "\n\n"
        return s

    def to_timer_objs(self, by_round=False, env=None, eval_exprs=False):
        times, seq_strs = [], []
        for rep, seq, rest in self.to_list():
            reps_type = type(rep)
            if (
                not by_round
                and not any([type(mvmt.magnitude) == Time for mvmt in seq.movements])
                and not seq.rest
                and not reps_type == Variable
            ):
                # add time and mvmt_seq
                times = times + [datetime.timedelta(0)]
                s = rep.__str__() + ":\n" + seq.to_str(include_rest=False) + "\n"
                seq_strs = seq_strs + [s]
            else:
                if any([type(mvmt.magnitude) == Time for mvmt in seq.movements]):
                    num_rds = rep.magnitude.eval_exprs()
                    mvmt_list = seq.to_list()
                    for j in range(num_rds):
                        s = "round " + str(j + 1) + " of " + str(num_rds) + ":\n"
                        num_mvmts = len(mvmt_list)
                        for k in range(num_mvmts):
                            mvmt = mvmt_list[k]
                            if not type(mvmt) == Rest:
                                times += [
                                    datetime.timedelta(
                                        **mvmt.magnitude.to_dict(env=env)
                                    )
                                ]
                                seq_strs += [
                                    s
                                    + (
                                        "movement "
                                        + str(k + 1)
                                        + " of "
                                        + str(num_mvmts)
                                        + ":\n"
                                    )
                                    + mvmt.__str__()
                                    + "\n"
                                ]
                            else:
                                times += [
                                    datetime.timedelta(
                                        **mvmt.magnitude.to_dict(env=env)
                                    )
                                ]
                                seq_strs += [s + "rest"]
                elif reps_type == Repetition:
                    num_rds = rep.magnitude.eval_exprs()
                    mvmt_list = seq.to_list()
                    for j in range(num_rds):
                        s = "round " + str(j + 1) + " of " + str(num_rds) + ":\n"
                        for mvmt in mvmt_list:
                            if not type(mvmt) == Rest:
                                times = times + [datetime.timedelta(0)]
                                seq_strs += [
                                    s + seq.to_str(include_rest=False) + "\n"
                                ]
                            else:
                                times += [
                                    datetime.timedelta(
                                        **mvmt.magnitude.to_dict(env=env)
                                    )
                                ]
                                seq_strs += [s + "rest"]
                elif reps_type == Variable:
                    var_name = rep.name
                    int_list = rep.ints
                    num_rds = len(int_list)
                    for j in range(num_rds):
                        times += [datetime.timedelta(0)]
                        s = ("round " + str(j + 1) + " of " + str(num_rds) + ":\n"
                             + seq.to_str(
                                    include_rest=False,
                                    env={var_name: int_list[j]},
                                    eval_exprs=True,
                                )
                            + "\n"
                        )
                        seq_strs += [s]
                        if seq.rest:
                            times += [
                                datetime.timedelta(
                                    **seq.rest[j].magnitude.to_dict(env=env)
                                )
                            ]
                            seq_strs += ["rest"]
            if rest:
                times += [rest.get_time().to_timedelta()]
                seq_strs += ["rest"]
        return list(zip(times, seq_strs))

    def to_ir(self, top=False):
        ir = {
            "TaskPriorityBase": {
                "reps": [r.to_ir() for r in self.reps],
                "seq": [s.to_ir() for s in self.seq],
                "rest": [r.to_ir() for r in self.rest],
            }
        }
        if top:
            return {
                "type": "TaskPriorityBase",
                "ir": ir,
                "timer_objs": [(t.seconds, s) for t, s in self.to_timer_objs()],
                "str": self.__str__(),
            }
        else:
            return ir

    def __str__(self):
        return self.to_str()

    def __repr__(self):
        return (
            "<" + self.cls_name() + "([" + ",".join(map(repr, self.to_list())) + "])>"
        )

    @classmethod
    def from_ir(cls, ir):
        return cls(
            reps=[cls.textx_type_class(r).from_ir(r) for r in ir.reps],
            seq=[cls.textx_type_class(s).from_ir(s) for s in ir.seq],
            rest=[cls.textx_type_class(r).from_ir(r) for r in ir.rest],
        )
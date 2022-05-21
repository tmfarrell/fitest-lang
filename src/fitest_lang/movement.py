import datetime
import itertools as it
import sys
from types import FunctionType

from .baseobject import FitestObject, FitestBaseObject
from .expression import Value, Variable
from .quantity import Quantity, Work, Time, Weight, Length, Repetition


class MovementBase(FitestBaseObject, FitestObject):
    @staticmethod
    def textx_type_class(textx_type):
        t = str(textx_type)
        if 'Value' in t:
            return Value
        elif 'Variable' in t:
            return Variable
        elif 'Work' in t:
            return Work
        elif 'Time' in t:
            return Time
        elif 'Weight' in t:
            return Weight
        elif 'Length' in t:
            return Length
        else:
            t = t[t.find(".") + 1: t.find(" ")]
            return getattr(sys.modules[__name__], t)


class Rest(MovementBase):
    def __init__(self, magnitude):
        self.magnitude = magnitude

    def get_time(self, env={}):
        return self.magnitude.eval_exprs(env=env)

    def get_reps(self, rep_len=Quantity(15, "sec")):
        return int(
            Quantity(self.magnitude.magnitude.eval_exprs(), self.magnitude.units)
            / rep_len
        )

    def to_ir(self):
        return {"Rest": self.magnitude.to_ir()}

    def __str__(self):
        return self.magnitude.to_str() + " rest"

    def __repr__(self):
        return "<" + self.cls_name() + "(" + self.magnitude.__repr__() + ")>"

    @classmethod
    def from_ir(cls, ir):
        return cls(cls.textx_type_class(ir.magnitude).from_ir(ir.magnitude))


class MovementSeq(MovementBase):
    def __init__(self, movements, rest=None):
        self.movements = movements
        self.rest = rest
        self.valid = all([m.task_priority for m in movements]) or all(
            [m.time_priority for m in movements]
        )
        assert self.valid, "movement seq is invalid."
        self.time_priority = self.movements[0].time_priority
        self.task_priority = not self.time_priority

    def get_time(self, env={}, by_mvmt=False):
        ts = [m.get_time(env=env) for m in self.movements]
        if by_mvmt:
            if len(self.rest) == 1:
                return ts + [self.rest[0].get_time()]
            else:
                return [
                    x
                    for x in it.chain(
                        *it.zip_longest(ts, [r.get_time() for r in self.rest])
                    )
                    if not x is None
                ]
        else:
            if not self.rest:
                return np.sum(ts)
            elif len(self.rest) == 1:
                return (np.sum(ts), self.rest[0].get_time())
            else:
                return [
                    x
                    for x in it.chain(
                        *it.zip_longest(ts, [r.get_time() for r in self.rest])
                    )
                    if not x is None
                ]

    def get_reps(self, env={}):
        return [m.get_reps(env=env) for m in self.movements]

    def get_work(self, athlete, env={}, work_units="cal", by_mvmt=False):
        mvmt_works = [mvmt.get_work(athlete, env=env) for mvmt in self.movements]
        if any([type(mw) == FunctionType for mw in mvmt_works]):

            def work_fcn(scores):
                assert len(scores) == len(
                    mvmt_works
                ), "scores need to correspond one-to-one to mvmts"
                work = []
                for score, mvmt_work in zip(scores, mvmt_works):
                    if type(mvmt_work) == FunctionType:
                        work = work + [mvmt_work(score).to(work_units)]
                    else:
                        work = work + [mvmt_work.to(work_units)]
                if not by_mvmt:
                    return sum(work)
                else:
                    return work

            return work_fcn
        else:
            return sum(mvmt_works).to(work_units)

    def describe(self, env={}, by="mvmt_category"):
        d = {}
        for m in self.to_list():
            # get key
            if not type(m) == Rest:
                if by == "mvmt_category":
                    key = m.get_mvmt_category()
                elif by == "mvmt_type":
                    key = m.mvmt_type
                    if not type(key) == str:
                        key = key.mvmt_type
                elif by == "mvmt_emphasis":
                    key = m.get_mvmt_emphasis()
            else:
                key = "rest"
            # get value
            val = m.get_time(env=env) if self.time_priority else m.get_reps(env=env)
            # add to description dict
            if not key in d.keys():
                d[key] = val
            else:
                d[key] = d[key] + val
        total = np.sum(list(d.values()))
        return {k: round(v / total, 3) for k, v in d.items()}

    def to_list(self):
        if len(self.rest) > 1:
            return [
                x
                for x in it.chain(*it.zip_longest(self.movements, self.rest))
                if not x is None
            ]
        elif len(self.rest) == 1:
            return self.movements + self.rest
        else:
            return self.movements

    def mvmt_reps_list(self):
        return [m.magnitude for m in self.movements]

    def to_timer_objs(self, env=None, eval_exprs=False):
        s = ""
        times, seq_strs = [], []
        if len(self.rest) > 1:
            for (mvmt, rest) in it.zip_longest(self.movements, self.rest):
                if type(mvmt.magnitude) != Time:
                    times = times + [datetime.timedelta(seconds=0)]
                    seq_strs = seq_strs + [mvmt.to_str(env=env, eval_exprs=eval_exprs)]
                else:
                    times = times + [datetime.timedelta(**mvmt.magnitude.to_dict())]
                    seq_strs = seq_strs + [mvmt.to_str(env=env, eval_exprs=eval_exprs)]
                if rest:
                    times = times + [datetime.timedelta(**rest.magnitude.to_dict())]
                    seq_strs = seq_strs + ["rest"]
        else:
            for mvmt in self.movements:
                if type(mvmt.magnitude) != Time:
                    times = times + [datetime.timedelta(seconds=0)]
                    seq_strs = seq_strs + [mvmt.to_str(env=env, eval_exprs=eval_exprs)]
                else:
                    times = times + [datetime.timedelta(**mvmt.magnitude.to_dict())]
                    seq_strs = seq_strs + [mvmt.to_str(env=env, eval_exprs=eval_exprs)]
            if self.rest and include_rest:
                times = times + [datetime.timedelta(**self.rest[0].magnitude.to_dict())]
                seq_strs = seq_strs + ["rest"]
        return list(zip(times, seq_strs))

    def to_str(self, include_rest=True, env=None, eval_exprs=False):
        s = ""
        classes = globals()
        if len(self.rest) > 1:
            for (mvmt, rest) in it.zip_longest(self.movements, self.rest):
                s = s + mvmt.to_str(env=env, eval_exprs=eval_exprs) + "\n"
                if rest:
                    s = (
                        s
                        + rest.magnitude.to_str(env=env, eval_exprs=eval_exprs)
                        + " rest\n"
                    )
        else:
            for mvmt in self.movements:
                s = s + mvmt.to_str(env=env, eval_exprs=eval_exprs) + "\n"
            if self.rest and include_rest:
                s = (
                    s
                    + self.rest[0].magnitude.to_str(env=env, eval_exprs=eval_exprs)
                    + " rest\n"
                )
        return s

    def to_ir(self, top=False):
        ir = {
            "MovementSeq": {
                "rest": [r.to_ir() for r in self.rest],
                "movements": [m.to_ir() for m in self.movements],
            }
        }
        if top:
            return {
                "type": "MovementSeq",
                "timer_objs": [(t.seconds, s) for t, s in self.to_timer_objs()],
                "str": self.__str__(),
                "ir": ir,
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
            movements=[cls.textx_type_class(m).from_ir(m) for m in ir.movements],
            rest=[cls.textx_type_class(r).from_ir(r) for r in ir.rest],
        )


class Movement(MovementBase):
    def get_mvmt_category(self):
        cls_name = self.cls_name()
        return cls_name[: re.search("Movement", cls_name).start()].lower()


class EnduranceMovement(Movement):
    def __init__(self, magnitude, mvmt_type):
        self.magnitude = magnitude
        self.mvmt_type = mvmt_type
        self.time_priority = type(magnitude) == Time
        self.task_priority = not self.time_priority

    def get_time(self, env={}):
        if type(self.magnitude) == Time:
            return self.magnitude.eval_exprs(env=env)
        else:
            return Time()

    def get_reps(
        self, env={}, len_rep=Quantity(25, "meter"), work_rep=Quantity(1, "cal")
    ):
        if type(self.magnitude) != Time:
            m = self.magnitude.eval_exprs(env=env)
            if type(m) == Length:
                return int(Quantity(m.magnitude, m.units).to("meter") / len_rep)
            elif type(m) == Work:
                return int(Quantity(m.magnitude, m.units).to("cal") / work_rep)
            else:
                return m
        else:
            return Repetition()

    def get_mvmt_emphasis(self):
        return {
            "run": "lower",
            "swim": "full",
            "bike": "lower",
            "ski": "full",
            "airbike": "full",
            "row": "full",
        }[self.mvmt_type]

    def get_magnitude(self, env={}):
        m = self.magnitude.eval_exprs(env=env)
        return Quantity(m.magnitude, m.units)

    def get_work(self, athlete, env={}):
        magnitude = self.magnitude.eval_exprs(env=env)
        # print('magnitude of type: ' + str(type(magnitude)))
        if type(magnitude) == Work:
            return magnitude
        elif type(magnitude) == Time:

            def work_fcn(score):
                if self.mvmt_type in ["swim", "bike"]:
                    return EnduranceMovement(score, self.mvmt_type).get_work(
                        athlete, env=env
                    )(magnitude)
                else:
                    return EnduranceMovement(score, self.mvmt_type).get_work(
                        athlete, env=env
                    )

            return work_fcn
        elif type(magnitude) == Length:
            if self.mvmt_type == "run":
                return Quantity(
                    (
                        0.45
                        * athlete.get_weight(as_force=False).to("kg")
                        * magnitude.to_quantity().to("km")
                    ).magnitude,
                    "cal",
                )
            elif self.mvmt_type == "swim":

                def work_fcn(time):
                    q = Quantity(
                        0.55
                        * (
                            (magnitude.to_quantity() / time.to_quantity().to("sec")).to(
                                "feet / sec"
                            )
                            ** 2
                        ).magnitude,
                        "force_pound",
                    ) * magnitude.to_quantity().to("ft")
                    return q

                return work_fcn
            elif self.mvmt_type == "bike":

                def work_fcn(time):
                    g = Quantity(9.88, "m / s**2")
                    m = athlete.get_weight(as_force=False)
                    t = time.to_quantity().to("sec")
                    air_density = Quantity(1.225, "kg / m**3")
                    athlete_cross_sectional_area = Quantity(0.075, "m**2")
                    v = magnitude.to_quantity().to("meter") / t
                    fric_coeff_air = 1
                    fric_coeff_road = 0.005
                    work = (
                        (0.5 * air_density * athlete_cross_sectional_area * v ** 3 * t)
                        + (v * m * g * fric_coeff_road * t)
                        + (v * m * v)
                    )
                    return work

                return work_fcn
            else:
                """elif self.mvmt_type == 'ski':
                pass
                elif self.mvmt_type == 'airbike':
                pass
                elif self.mvmt_type == 'row':
                pass"""
                return Quantity(0, "cal")

    def to_str(self, env=None, eval_exprs=False):
        try:
            return (
                self.magnitude.to_str(env=env, eval_exprs=eval_exprs)
                + " "
                + self.mvmt_type.to_str(env=env, eval_exprs=eval_exprs)
            )
        except:
            return str(self.magnitude) + " " + str(self.mvmt_type)

    def to_ir(self):
        return {
            "EnduranceMovement": {
                "magnitude": self.magnitude.to_ir(),
                "mvmt_type": self.mvmt_type,
            }
        }

    def __str__(self):
        mt = (
            self.mvmt_type.to_str()
            if not type(self.mvmt_type) == str
            else self.mvmt_type
        )
        return self.magnitude.to_str() + " " + mt

    def __repr__(self):
        return (
            "<"
            + self.cls_name()
            + "("
            + self.magnitude.__repr__()
            + ","
            + self.mvmt_type
            + ")>"
        )

    @classmethod
    def from_ir(cls, ir):
        return cls(
            magnitude=cls.textx_type_class(ir.magnitude).from_ir(ir.magnitude),
            mvmt_type=ir.mvmt_type.mvmt_type,
        )


class ObjectMovement(Movement):
    def __init__(self, magnitude, weight, obj, mvmt_type, height, time=None):
        self.magnitude = magnitude
        self.weight = weight
        self.obj = obj
        self.mvmt_type = mvmt_type
        self.height = height
        self.time_priority = type(magnitude) == Time
        self.task_priority = not self.time_priority

    def get_time(self, env={}):
        if type(self.magnitude) == Time:
            return self.magnitude.eval_exprs(env=env)
        else:
            return Time()

    def get_reps(self, env={}):
        if type(self.magnitude) != Time:
            return self.magnitude.eval_exprs(env=env)
        else:
            return Repetition()

    def get_mvmt_emphasis(self):
        return {
            "clean": "lower",
            "clean_and_jerk": "full",
            "front_squat": "lower",
            "deadlift": "lower",
            "sumodeadlift": "lower",
            "sumodeadlift_highpull": "full",
            "push_press": "upper",
            "push_jerk": "upper",
            "split_jerk": "upper",
            "shoulder_to_overhead": "upper",
            "ground_to_overhead": "full",
            "hang_clean": "lower",
            "thruster": "full",
            "back_squat": "lower",
            "bench_press": "upper",
            "swing": "full",
            "wallball": "full",
        }[self.mvmt_type]

    def get_work(self, athlete, env={}):
        magnitude = self.magnitude.eval_exprs(env=env)
        if type(magnitude) == Time:

            def work_fcn(score):
                return ObjectMovement(
                    score, self.weight, self.obj, self.mvmt_type, self.height
                ).get_work(athlete, env=env)

            return work_fcn
        elif type(magnitude) == Repetition or type(magnitude) == int:
            # if from the floor
            if self.mvmt_type in [
                "clean",
                "snatch",
                "deadlift",
                "sumodeadlift",
                "sumodeadlift_highpull",
                "ground_to_overhead",
            ]:
                # set initial height as height of object
                if self.obj == "barbell":
                    height_initial = Quantity(17.72, "in")
                elif "dumbbell" in self.obj:
                    height_initial = Quantity(4.5, "in")
                elif "kettlebell" in self.obj:
                    height_initial = Quantity(5.5, "in")
                # set final height according to mvmt
                if self.mvmt_type in ["deadlift", "sumodeadlift"]:
                    height_final = (
                        athlete.get_shoulder_height() - athlete.get_arm_length()
                    )
                elif self.mvmt_type in ["clean", "sumodeadlift_highpull"]:
                    height_final = athlete.get_shoulder_height()
                elif self.mvmt_type in ["snatch", "ground_to_overhead"]:
                    height_final = (
                        athlete.get_shoulder_height() + athlete.get_arm_length()
                    )
                return magnitude * (
                    (self.weight.to_quantity() * Quantity("g_0")).to("force_pound")
                    * (height_final - height_initial)
                )
            # if from front rack
            elif self.mvmt_type in [
                "push_press",
                "push_jerk",
                "back_squat",
                "hang_clean",
                "front_squat",
                "thruster",
                "overhead_squat",
                "wallball",
            ]:
                # set mvmt distance
                if self.mvmt_type in ["push_press", "push_jerk", "hang_clean"]:
                    distance = athlete.get_arm_length()
                elif "squat" in self.mvmt_type:
                    distance = (
                        athlete.get_shoulder_height()
                        - athlete.get_squat_bottom_height()
                    )
                elif self.mvmt_type == "thruster":
                    distance = (
                        athlete.get_shoulder_height()
                        - athlete.get_squat_bottom_height()
                    ) + athlete.get_arm_length()
                elif self.mvmt_type == "wallball":
                    distance = (
                        self.height.to_quantity() - athlete.get_squat_bottom_height()
                    )
                return magnitude * (
                    (self.weight.to_quantity() * Quantity("g_0")).to("force_pound")
                    * distance
                )

    def to_str(self, env=None, eval_exprs=False):
        if not self.height:
            return (
                self.magnitude.to_str(env=env, eval_exprs=eval_exprs)
                + " "
                + self.weight.to_str(env=env, eval_exprs=eval_exprs)
                + " "
                + self.obj
                + " "
                + self.mvmt_type
            )
        else:
            return (
                self.magnitude.to_str(env=env, eval_exprs=eval_exprs)
                + " "
                + self.weight.to_str(env=env, eval_exprs=eval_exprs)
                + " "
                + self.height.to_str(env=env)
                + " "
                + self.mvmt_type
            )

    def to_ir(self):
        return {
            "ObjectMovement": {
                "magnitude": self.magnitude.to_ir(),
                "weight": self.weight.to_ir(),
                "object": self.obj,
                "height": self.height.to_ir() if not self.height is None else None,
                "mvmt_type": self.mvmt_type,
            }
        }

    def __str__(self):
        return self.to_str()

    def __repr__(self):
        if not self.height:
            return (
                "<"
                + self.cls_name()
                + "("
                + ",".join(
                    [
                        self.magnitude.__repr__(),
                        self.weight.__repr__(),
                        self.obj,
                        self.mvmt_type,
                    ]
                )
                + ")>"
            )
        else:
            return (
                "<"
                + self.cls_name()
                + "("
                + ",".join(
                    [
                        self.magnitude.__repr__(),
                        self.weight.__repr__(),
                        self.height.__repr__(),
                        self.mvmt_type,
                    ]
                )
                + ")>"
            )

    @classmethod
    def from_ir(cls, ir):
        return cls(
            obj=ir.mvmt_type.obj,
            mvmt_type=ir.mvmt_type.mvmt_type,
            magnitude=cls.textx_type_class(ir.magnitude).from_ir(ir.magnitude),
            weight=cls.textx_type_class(ir.mvmt_type.weight).from_ir(
                ir.mvmt_type.weight
            ),
            height=(
                cls.textx_type_class(ir.mvmt_type.height).from_ir(ir.mvmt_type.height)
                if ir.mvmt_type.height
                else None
            ),
        )


class GymnasticMovement(Movement):
    def __init__(self, magnitude, mvmt_type, time=None):
        self.magnitude = magnitude
        self.mvmt_type = mvmt_type
        self.time_priority = type(magnitude) == Time
        self.task_priority = not self.time_priority

    def get_time(self, env={}):
        if type(self.magnitude) == Time:
            return self.magnitude.eval_exprs(env=env)
        else:
            return Time()

    def get_reps(self, env={}, rep_len=Quantity(10, "ft")):
        if type(self.magnitude) != Time:
            m = self.magnitude.eval_exprs(env=env)
            if type(m) == Length:
                return int(Quantity(m.magnitude, m.units).to("ft") / rep_len)
            else:
                return m
        else:
            return Repetition()

    def get_mvmt_emphasis(self):
        return {
            "pushup": "upper",
            "pullup": "upper",
            "burpee": "full",
            "burpee_pullup": "full",
            "situp": "midline",
            "ghd_situp": "midline",
            "dip": "upper",
            "muscle_up": "upper",
            "pistol": "lower",
            "squat": "lower",
            "handstand_pushup": "upper",
            "double_under": "full",
            "toe_to_bar": "midline",
            "knee_to_elbow": "midline",
            "back_extension": "midline",
            "hip_extension": "midline",
            "box_jump": "lower",
        }[self.mvmt_type.mvmt_type]

    def get_work(self, athlete, env={}):
        magnitude = self.magnitude.eval_exprs(env=env)
        if type(magnitude) == Time:

            def work_fcn(score):
                return GymnasticMovement(score, self.mvmt_type).get_work(
                    athlete, env=env
                )

            return work_fcn
        elif type(magnitude) == Repetition or type(magnitude) == int:
            if self.mvmt_type.mvmt_type == "pushup":
                return (
                    magnitude
                    * (0.6 * athlete.get_weight())
                    * (0.6 * athlete.get_arm_length())
                )
            elif self.mvmt_type.mvmt_type in ["pullup", "dip", "handstand_pushup"]:
                return magnitude * athlete.get_weight() * athlete.get_arm_length()
            elif self.mvmt_type.mvmt_type == "burpee":
                return (
                    magnitude
                    * athlete.get_weight()
                    * (0.6 * athlete.get_height() + Quantity(3, "in"))
                )
            elif self.mvmt_type.mvmt_type == "burpee_pullup":
                return (
                    magnitude
                    * athlete.get_weight()
                    * (0.6 * athlete.get_height() + athlete.get_arm_length())
                )
            elif self.mvmt_type.mvmt_type == "situp":
                return (
                    magnitude
                    * (0.4 * athlete.get_weight())
                    * (0.25 * athlete.get_height())
                )
            elif self.mvmt_type.mvmt_type == "ghd_situp":
                return (
                    magnitude
                    * (0.5 * athlete.get_weight())
                    * (0.5 * athlete.get_height())
                )
            elif self.mvmt_type.mvmt_type == "muscle_up":
                return magnitude * athlete.get_weight() * (2 * athlete.get_arm_length())
            elif self.mvmt_type.mvmt_type in ["pistol", "squat"]:
                return (
                    magnitude
                    * athlete.get_weight()
                    * (athlete.get_height() - athlete.get_squat_bottom_height())
                )
            elif self.mvmt_type.mvmt_type == "double_under":
                return magnitude * athlete.get_weight() * Quantity(3, "in")
            elif self.mvmt_type.mvmt_type == "box_jump":
                return (
                    magnitude
                    * athlete.get_weight()
                    * self.mvmt_type.height.to_quantity()
                )

    def __str__(self):
        return self.to_str()

    def __repr__(self):
        return (
            "<"
            + self.cls_name()
            + "("
            + self.magnitude.__repr__()
            + ","
            + self.mvmt_type.__repr__()
            + ")>"
        )

    def to_ir(self):
        return {
            "GymnasticMovement": {
                "magnitude": self.magnitude.to_ir(),
                "mvmt_type": self.mvmt_type.to_ir(),
            }
        }

    def to_str(self, env=None, eval_exprs=False):
        return (
            self.magnitude.to_str(env=env, eval_exprs=eval_exprs)
            + " "
            + self.mvmt_type.to_str(env=env, eval_exprs=eval_exprs)
        )

    @classmethod
    def from_ir(cls, ir):
        return cls(
            magnitude=cls.textx_type_class(ir.magnitude).from_ir(ir.magnitude),
            mvmt_type=cls.textx_type_class(ir.mvmt_type).from_ir(ir.mvmt_type),
        )


class GymnasticMovementType(MovementBase):
    def __init__(self, mvmt_type, height=None):
        self.mvmt_type = mvmt_type
        self.height = height

    def to_str(self, env=None, eval_exprs=False):
        if not self.height:
            return self.mvmt_type
        else:
            return (
                self.height.to_str(env=env, eval_exprs=eval_exprs)
                + " "
                + self.mvmt_type
            )

    def to_ir(self):
        return {
            "GymnasticMovementType": {
                "mvmt_type": self.mvmt_type,
                "height": self.height.to_ir() if not self.height is None else None,
            }
        }

    def __str__(self):
        return self.to_str()

    def __repr__(self, env=None, eval_exprs=False):
        if not self.height:
            return "<" + self.cls_name() + "(" + self.mvmt_type + ")>"
        else:
            return (
                "<"
                + self.cls_name()
                + "("
                + self.height.to_str(env=env, eval_exprs=eval_exprs)
                + ","
                + self.mvmt_type
                + ")>"
            )

    @classmethod
    def from_ir(cls, ir):
        return cls(
            ir.mvmt_type,
            cls.textx_type_class(ir.height).from_ir(ir.height) if ir.height else None,
        )

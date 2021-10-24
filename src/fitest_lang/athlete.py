from .baseobject import FitestBaseObject
from .quantity import Quantity, Length, Weight


class Athlete(FitestBaseObject):
    def __init__(
        self,
        name,
        weight,
        height,
        shoulder_height=None,
        arm_length=None,
        squat_bottom_height=None,
    ):
        self.name = name
        assert type(weight) == Weight, "weight be of type: Weight"
        self.weight = Quantity(weight.magnitude, weight.units)
        assert type(height) == Length, "height be of type: Length"
        self.height = Quantity(height.magnitude, height.units)
        if shoulder_height is None:
            self.shoulder_height = 0.75 * Quantity(height.magnitude, height.units)
        else:
            assert type(shoulder_height) == Length, "shoulder_height be of type: Length"
            self.shoulder_height = Quantity(
                shoulder_height.magnitude, shoulder_height.units
            )
        if arm_length is None:
            self.arm_length = 0.4 * Quantity(height.magnitude, height.units)
        else:
            assert type(arm_length) == Length, "arm_height be of type: Length"
            self.arm_length = Quantity(arm_length.magnitude, arm_length.units)
        if squat_bottom_height is None:
            self.squat_bottom_height = 0.45 * Quantity(height.magnitude, height.units)
        else:
            assert type(squat_bottom_height) == Length, "height be of type: Length"
            self.squat_bottom_height = Quantity(
                squat_bottom_height.magnitude, squat_bottom_height.units
            )

    def get_height(self):
        return self.height

    def get_weight(self, as_force=True):
        if as_force:
            return (self.weight * Quantity("g_0")).to("force_pound")
        else:
            return self.weight

    def get_squat_bottom_height(self):
        return self.squat_bottom_height

    def get_arm_length(self):
        return self.arm_length

    def get_shoulder_height(self):
        return self.shoulder_height

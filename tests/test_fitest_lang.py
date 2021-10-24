import importlib.resources

import pytest
import textx

from fitest_lang.athlete import Athlete
import fitest_lang.config
from fitest_lang.program import Program
from fitest_lang.quantity import Weight, Length


TEST_PROGRAMS = [
    "1000 meter swim",
    "5 km run",
    "20 mile bike",
    "20 min swim\n20 min bike",
    "4 rounds:\n400 meter run\n75 meter swim\n1 min rest ;",
    "AMRAP 18 min:\n600 meter run\n100 meter swim ;",
    "2 km row\n1 mile run\n2 km row",
    "400 meter run\n90 sec rest\n200 meter run\n60 sec rest\n100 meter run",
    "AMRAP 20 min:\n5 handstand_pushup\n10 pistol\n15 pullup ;",
    "AMRAP 20 min:\n5 pullup\n10 pushup\n15 squat ;",
    "5 rounds:\n400 meter run\n15 95 lb barbell overhead_squat ;",
    "3 rounds:\n50 squat\n7 muscle_up\n10 135 lb barbell hang_clean ;",
    "3 rounds:\n50 squat\n7 muscle_up\n10 135 lb barbell hang_clean ;\n\n5 min rest\n\n"
    + "3 rounds:\n25 squat\n3 muscle_up\n5 135 lb barbell hang_clean ;",
    "150 20 lb 14 ft wallball",
    "5 rounds:\n1 min 20 lb 14 ft wallball\n1 min airbike\n1 min double_under\n1 min rest ;",
    "1500 meter row\n50 45 lb barbell thruster\n30 pullup",
    "5 rounds:\n400 meter run\n30 20 inch box_jump\n30 20 lb 14 ft wallball ;",
    "4 rounds:\nAMRAP 4 min:\n15 cal row\n15 20 lb 14 ft wallball\n15 pullup ;\n4 min rest ;",
    "for N in 21 15 9:\nN 95 lb barbell thruster\nN pullup ;",
    "for N1 in 21 15 9:\nN1 95 lb barbell thruster\nN1 pullup ;\n3 min rest\n\n"
    + "for N2 in 15 12 9:\nN2 135 lb barbell thruster\nN2 burpee ;",
    "for round in 4 3 2 1:\nAMRAP 4 min:\n(5 * round) cal row"
    + "\n(5 * round) 20 lb 14 ft wallball\n(5 * round) pullup ;\n4 min rest ;",
    "AMRAP 4 min:\n10 cal row\n10 20 lb 14 ft wallball\n10 pullup ;\n\n2 min rest"
    + "\n\nAMRAP 4 min:\n15 cal row\n15 20 lb 14 ft wallball\n15 pullup ;\n\n2 min rest"
    + "\n\nAMRAP 4 min:\n20 cal row\n20 20 lb 14 ft wallball\n20 pullup ;",
    "for N in 100 80 60 40 20:\nN double_under\n(N / 2) situp\n(N / 10) 225 lb barbell deadlift ;",
]

TEST_ATHLETE = Athlete("Tim", Weight(160, "lb"), Length(67, "in"))

def load_dsl():
    with importlib.resources.path(fitest_lang.config, 'dsl.tx') as path:
        return textx.metamodel_from_file(path)

DSL = load_dsl()

@pytest.mark.parametrize("program_str", TEST_PROGRAMS)
def test_dsl(program_str):
    print('\n\n' + program_str)
    r = DSL.model_from_str(program_str)
    print("\nvalid: " + str(r))
    return

@pytest.mark.parametrize("program_str", TEST_PROGRAMS)
def test_str_to_ir(program_str):
    print("\ntest:\n" + program_str + "\n")
    s = Program.ir_to_str(DSL.model_from_str(program_str)).strip()
    print("ir_to_str:\n" + s + "\n")
    print("test == ir_to_str: " + str(program_str == s))
    print()
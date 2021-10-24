import datetime
import importlib.resources
import sys
import time
from select import select

import textx

from . import config
from .movement import MovementSeq
from .program import Program
from .quantity import PhysicalQuantity, Repetition, Weight, Length


# utils
def parse(s):
    with importlib.resources.path(config, 'dsl.tx') as path:
        dsl = textx.metamodel_from_file(path)
    program = dsl.model_from_str(s)
    return program


# evaluate
# takes program string and returns (time_in_secs, count_down_or_up, program_str)
def evaluate(s):
    program = parse(s)
    return Program.ir_to_timer_objs(program)


def run_timer_objs(timer_objs_n_seq_strs):
    timeout = 1
    scores, times = [], []
    for timer_obj, seq_str in timer_objs_n_seq_strs:
        if timer_obj.seconds == 0:
            while True:
                print(str(timer_obj) + "\n" + seq_str + "\n")
                result, _, _ = select([sys.stdin], [], [], timeout)
                if result:
                    s = sys.stdin.readline()
                    if "round" in s:
                        print("\ntime: " + str(timer_obj) + "\n")
                        times = times + [timer_obj]
                        scores += [
                            MovementSeq(
                                acta_parse(seq_str[seq_str.find(":") + 1 :])
                            ).mvmt_reps_list()
                        ]
                        try:
                            rounds = Repetition(
                                PhysicalQuantity.str_to_ir(seq_str[: seq_str.find(":")])
                            )
                            if rounds.magnitude == len(scores):
                                break
                        except:
                            break
                # time.sleep(1)
                timer_obj = timer_obj + datetime.timedelta(seconds=timeout)
        else:
            score = 0
            splits, round_split = [], datetime.timedelta(seconds=0)
            while True:
                print(str(timer_obj) + "\n" + seq_str + "\n")
                result, _, _ = select([sys.stdin], [], [], timeout)
                if result:
                    s = sys.stdin.readline()
                    if "round" in s and seq_str != "rest":
                        score = score + 1
                        print("\nscore: " + str(score) + "\n")
                        print("\nsplit: " + str(round_split) + "\n")
                        splits = splits + [round_split]
                        round_split = datetime.timedelta(seconds=0)
                timer_obj = timer_obj - datetime.timedelta(seconds=timeout)
                round_split = round_split + datetime.timedelta(seconds=timeout)
                if timer_obj.days < 0:
                    if seq_str != "rest":
                        scores = scores + [score]
                        times = times + [splits]
                        print("\nscore: " + str(score) + "\n")
                    break
    print("scores: " + str(scores))
    # print('avg scores: ' + str(np.mean(scores)))
    # print('total scores: ' + str(np.sum(scores)) + '\n')
    print("times: " + str(times))
    return (scores, times)


def evaluate_on_cmd_line(s):
    acta = textx.metamodel_from_file("acta_grammar.tx")
    program = acta.model_from_str(s)
    program_cls = str(program)
    program_cls = program_cls[program_cls.find(".") + 1 : program_cls.find(" ")]
    if program_cls in ["TaskPriority", "MovementSeq"]:
        # just start a timer
        t = datetime.timedelta()
        # and display the program
        while True:
            print(str(t) + "\n" + s + "\n")
            time.sleep(1)
            t = t + datetime.timedelta(seconds=1)
    elif program_cls in ["TimePriority", "TimeLimitedTask"]:
        # start countdown
        t = datetime.timedelta(**time_to_dict(program.time))
        # and display the program
        while str(t) != "00:00:00":
            print(str(t) + "\n" + s + "\n")
            time.sleep(1)
            t = t - datetime.timedelta(seconds=1)
    return




from dataclasses import dataclass
from datetime import timedelta
from typing import Union

@dataclass
class Timers:
    timers: list

    def to_json(self): 
        return [
            t.__dict__() for t in self.timers
        ]

    def to_list(self): 
        return self.timers


@dataclass
class Stopwatch:
    time: timedelta
    desc: str

    def __dict__(self): 
        return {
            'type': 'stopwatch',
            'time': self.time.__dict__(), 
            'desc': self.desc
        }


@dataclass
class Timer:
    time: timedelta
    desc: Union[str, Stopwatch]

    def __dict__(self): 
        return {
            'type': 'timer',
            'time': self.time.__dict__(), 
            'desc': self.desc
        }


@dataclass
class TimeCap:
    time: timedelta
    desc: Union[str, Stopwatch]

    def __dict__(self): 
        return {
            'type': 'timecap',
            'time': self.time.__dict__(), 
            'desc': self.desc
        }
        
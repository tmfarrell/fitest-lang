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
    desc: str

    def __dict__(self): 
        return {
            'type': 'stopwatch', 
            'desc': self.desc
        }


@dataclass
class Timer:
    time: timedelta
    desc: Union[str, Stopwatch]

    def __dict__(self): 
        return {
            'type': 'timer',
            'time': { 'seconds': self.time.total_seconds() }, 
            'desc': self.desc if type(self.desc) == str else self.desc.to_json()
        }


@dataclass
class TimeCap:
    time: timedelta
    desc: Union[str, Stopwatch]

    def __dict__(self): 
        return {
            'type': 'timecap',
            'time': { 'seconds': self.time.total_seconds() }, 
            'desc': self.desc if type(self.desc) == str else self.desc.to_json()
        }
        
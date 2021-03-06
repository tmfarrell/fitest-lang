
## fitest-lang

A DSL for converting human-readable functional fitness programs 
into data objects that can be saved and analyzed.

Here's an example: 

```python
$ poetry run ipython
Python 3.8.5 (default, Sep  4 2020, 02:22:02) 
Type 'copyright', 'credits' or 'license' for more information
IPython 7.28.0 -- An enhanced Interactive Python. Type '?' for help.

In [1]: import fitest_lang.dsl

In [2]: from fitest_lang.program import Program

In [3]: example = "for N in 21 15 9:\nN 95 lb barbell thruster\nN pullup ;"

In [4]: print('\n' + example)

for N in 21 15 9:
N 95 lb barbell thruster
N pullup ;

In [5]: p = Program.from_ir(fitest_lang.dsl.parse(example))

In [6]: print(p.to_json())
{
 "type": "TaskPriorityBase",
 "ir": {
  "TaskPriorityBase": {
   "reps": [
    {
     "Variable": {
      "name": "N",
      "ints": [
       21,
       15,
       9
      ]
     }
    }
   ],
   "seq": [
    {
     "MovementSeq": {
      "rest": [],
      "movements": [
       {
        "ObjectMovement": {
         "magnitude": {
          "Value": "N"
         },
         "weight": {
          "quantity.Weight": {
           "magnitude": {
            "Value": 95
           },
           "units": "lb"
          }
         },
         "object": "barbell",
         "height": null,
         "mvmt_type": "thruster"
        }
       },
       {
        "GymnasticMovement": {
         "magnitude": {
          "Value": "N"
         },
         "mvmt_type": {
          "GymnasticMovementType": {
           "mvmt_type": "pullup",
           "height": null
          }
         }
        }
       }
      ]
     }
    }
   ],
   "rest": []
  }
 }
}
```

### testing 

To run tests, do 

```bash
make test
```

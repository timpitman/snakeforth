import pytest
from fourth.fourth import FourthInterpreter

program_fact_loop = """
: factorial
   DUP 2 < IF DROP 1 EXIT THEN 
   DUP 
   BEGIN DUP 2 > WHILE 
   1- SWAP OVER * SWAP p
   REPEAT DROP 
;
"""
program_fact = """
    : factorial
      dup 1 >
      if
        dup 1 -
        factorial *
      else
        drop 1
      then
    ;
    """


@pytest.mark.parametrize("factorial_function", [program_fact, program_fact_loop])
def test_factorial(factorial_function):
    fi = FourthInterpreter()
    fi.parse(factorial_function)
    fi.parse("4 factorial")
    assert fi.stack == [24]
    fi.parse("1 factorial")
    assert fi.stack == [24, 1]


def test_if():
    # test adapted from forth standard: https://forth-standard.org/standard/testsuite#test:core:IF
    fi = FourthInterpreter()
    fi.parse(": GI1 IF 123 THEN ;")
    fi.parse(": GI2 IF 123 ELSE 234 THEN ;")
    fi.parse("0 GI1")
    assert fi.stack == []
    fi.parse("1 GI1")
    assert fi.stack == [123]
    fi.parse(". -1 GI1")
    assert fi.stack == [123]
    fi.parse(". 0 GI2")
    assert fi.stack == [234]
    fi.parse(". 1 GI2")
    assert fi.stack == [123]
    fi.parse(". -1 GI2")
    assert fi.stack == [123]

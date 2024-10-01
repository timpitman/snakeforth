import pytest
from snakeforth.snakeforth import ForthInterpreter

""" higher-level tests with some simple programs """

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
    # test an entire factorial function, using loop and recursive implementations
    fi = ForthInterpreter()
    fi.parse(factorial_function)
    fi.parse("4 factorial")
    assert fi.stack == [24]
    fi.parse("1 factorial")
    assert fi.stack == [24, 1]


def test_nested_control_structures():
    fi = ForthInterpreter()
    fi.parse("""
    : nested-test
      10 0
      BEGIN
        DUP 5 <
        IF
          1 +
        ELSE
          1 -
          DUP 0 =
          IF
            DROP TRUE
          ELSE
            FALSE
          THEN
        THEN
        SWAP 1 - SWAP
        OVER 0 =
      UNTIL
    ;
    """)
    fi.parse("nested-test")
    assert fi.stack == [5, 0, 3]
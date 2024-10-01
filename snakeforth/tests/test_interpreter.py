import pytest
from snakeforth.snakeforth import ForthInterpreter


def test_if():
    # test if statement
    # adapted from forth standard: https://forth-standard.org/standard/testsuite#test:core:IF
    fi = ForthInterpreter()
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


def test_stack_operations():
    fi = ForthInterpreter()
    fi.parse("1 2 3 dup")
    assert fi.stack == [1, 2, 3, 3]
    fi.parse("drop")
    assert fi.stack == [1, 2, 3]
    fi.parse("swap")
    assert fi.stack == [1, 3, 2]
    fi.parse("over")
    assert fi.stack == [1, 3, 2, 3]
    fi.parse("rot")
    assert fi.stack == [1, 2, 3, 3]


def test_arithmetic_operations():
    fi = ForthInterpreter()
    fi.parse("5 3 +")
    assert fi.stack == [8]
    fi.parse("10 4 -")
    assert fi.stack == [8, 6]
    fi.parse("3 *")
    assert fi.stack == [8, 18]
    fi.parse("2 /")
    assert fi.stack == [8, 9]
    fi.parse("7 mod")
    assert fi.stack == [8, 2]


def test_comparison_operations():
    fi = ForthInterpreter()
    fi.parse("5 3 <")
    assert fi.stack == [0]
    fi.parse("5 3 >")
    assert fi.stack == [0, -1]
    fi.parse("5 5 =")
    assert fi.stack == [0, -1, -1]


def test_bitwise_operations():
    fi = ForthInterpreter()
    fi.parse("5 3 and")
    assert fi.stack == [1]
    fi.parse("5 3 or")
    assert fi.stack == [1, 7]
    fi.parse("5 3 xor")
    assert fi.stack == [1, 7, 6]
    fi.parse("5 invert")
    assert fi.stack == [1, 7, 6, -6]


def test_variables_and_constants():
    fi = ForthInterpreter()
    fi.parse("variable myvar")
    fi.parse("10 myvar !")
    fi.parse("myvar @")
    assert fi.stack == [10]
    fi.parse("20 constant myconst")
    fi.parse("myconst")
    assert fi.stack == [10, 20]


def test_loops():
    fi = ForthInterpreter()
    fi.parse(": count-down 5 BEGIN DUP 0 > WHILE DUP 1 - REPEAT DROP ;")
    fi.parse("count-down")
    assert fi.stack == [5, 4, 3, 2, 1]


def test_comments():
    fi = ForthInterpreter()
    fi.parse("5 ( this is a comment ) 3 +")
    assert fi.stack == [8]
    fi.parse("10 \\ this is a line comment")
    assert fi.stack == [8, 10]






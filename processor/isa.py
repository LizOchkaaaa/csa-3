class Opcode:

    DUP = "dup"
    DROP = "drop"
    PUSH = "push"
    TOP = "top"
    CLEAR = "clear"

    LOAD = "load"
    IND_LOAD = "ind_load"
    STORE = "store"
    IND_STORE = "ind_store"

    ADD = "add"
    SUB = "sub"
    MUL = "mul"
    DIV = "div"
    MOD = "mod"
    INC = "inc"
    DEC = "dec"
    LESS_EQ = "less_eq"
    GREATER = "greater"
    EQUAL = "equal"
    NOT_EQUAL = "n_equal"

    JMP = "jmp"
    JIF = "jif"

    STOP = "stop"


class Term:
    DUP = "dup"
    DROP = "drop"
    CLEAR = "clear"

    EMIT = "emit"
    CR = "cr"
    KEY = "key"

    LOAD = "@"
    IND_LOAD = "@*"
    STORE = "!"
    IND_STORE = "!*"

    STRING = '"'
    IF = "if"
    ELSE = "else"
    END_IF = ";"
    PROCEDURE = ":"

    BEGIN = "begin"
    UNTIL = "until"

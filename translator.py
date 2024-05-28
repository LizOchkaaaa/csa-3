import json
import sys
import re
from processor.isa import Opcode, Term

INPUT_ADDRESS = 0
OUTPUT_ADDRESS = 1


def parse_math(row):
    return {
        "+": Opcode.ADD,
        "-": Opcode.SUB,
        "*": Opcode.MUL,
        "/": Opcode.DIV,
        "mod": Opcode.MOD,
        "++": Opcode.INC,
        "--": Opcode.DEC,
        "<=": Opcode.LESS_EQ,
        ">": Opcode.GREATER,
        "=": Opcode.EQUAL,
        "!=": Opcode.NOT_EQUAL,
    }.get(row)


def create_instruction(index, term, opcode, arg=None):
    instr = {"index": index, "term": term, "opcode": opcode}
    if arg is not None:
        instr["arg"] = arg
    return instr


def inverse_condition(opcode):
    return {
        Opcode.EQUAL: Opcode.NOT_EQUAL,
        Opcode.NOT_EQUAL: Opcode.EQUAL,
        Opcode.LESS_EQ: Opcode.GREATER,
        Opcode.GREATER: Opcode.LESS_EQ
    }.get(opcode)


def store_char(instructions, index, char):
    instructions.append(create_instruction(index, char, Opcode.TOP, ord(char)))
    instructions.append(create_instruction(index + 1, char, Opcode.STORE, OUTPUT_ADDRESS))
    return index + 2


def parse_string(instructions, code, index, start):
    instructions.append(create_instruction(index, ".", Opcode.DUP))
    index += 1
    stop = 0
    code[start] = code[start].replace(".", "", 1)
    for i in range(start, len(code)):
        row = code[i]
        for char in row:
            if char != Term.STRING:
                index = store_char(instructions, index, char)
        if row[-1] == Term.STRING:
            stop = i
            break
        else:
            index = store_char(instructions, index, " ")
    instructions.append(create_instruction(index, None, Opcode.DROP))
    return stop, index + 1


def cr_machine(index, instructions):
    instructions.extend((create_instruction(index, Term.CR, Opcode.PUSH, 10),
                         create_instruction(index + 1, Term.CR, Opcode.STORE, OUTPUT_ADDRESS),
                         create_instruction(index + 2, Term.CR, Opcode.DROP)))
    return index + 2


def check_variable(row, variables, variable_pointer):
    if row not in variables:
        variables[row] = variable_pointer
        variable_pointer += 1
    return variable_pointer


def next(i, code):
    try:
        return code[i + 1]
    except IndexError:
        return ""


def skip_comments(i, code):
    while "/" not in code[i]:
        i += 1
    return i + 1


def translator(code):
    instructions = []
    index = 1
    jump_buf = []

    procedures = {}
    in_procedure, parse_procedures = False, True

    variables = {}
    variable_pointer = 2

    instructions.append(create_instruction(0, "start", Opcode.JMP))
    for j in range(2):
        i = 0
        while i < len(code):
            if "/" in code[i]:
                i = skip_comments(i + 1, code)
                if i >= len(code):
                    break
            row = code[i]
            if row == Term.PROCEDURE:
                if not in_procedure:
                    in_procedure = True
                    if parse_procedures:
                        procedures[code[i + 1]] = index
                    i += 2
                else:
                    if parse_procedures:
                        instructions.append(create_instruction(index, Opcode.RET, Opcode.RET))
                        index += 1
                    in_procedure = False
                    i += 1
                continue

            if not in_procedure and parse_procedures or not parse_procedures and in_procedure:
                i += 1
                continue

            if Term.STRING in row:
                i, index = parse_string(instructions, code, index, i)
            elif row == Term.END_IF:
                instructions[jump_buf.pop()]["arg"] = index
            elif row == Term.BEGIN:
                jump_buf.append(index)

            else:
                if row == Term.IF:
                    jump_buf.append(index)
                    instructions[index - 1]["opcode"] = inverse_condition(instructions[index - 1]["opcode"])
                    instructions.append(create_instruction(index, Term.IF, Opcode.JIF))
                elif row == Term.ELSE:
                    label = jump_buf.pop()
                    jump_buf.append(index)
                    instructions.append(create_instruction(index, Term.ELSE, Opcode.JMP))
                    instructions[label]["arg"] = index + 1
                elif row == Term.UNTIL:
                    instructions.append(create_instruction(index, Term.UNTIL, Opcode.JIF, jump_buf.pop()))

                elif re.search("^-?[0-9]+$", row):
                    instructions.append(create_instruction(index, row, Opcode.PUSH, int(row)))
                elif parse_math(row) is not None:
                    instructions.append(create_instruction(index, row, parse_math(row)))

                elif row == Term.KEY:
                    instructions.append(create_instruction(index, Term.KEY, Opcode.LOAD, INPUT_ADDRESS))
                elif row in [Term.EMIT, Term.DOT]:
                    instructions.append(create_instruction(index, row, Opcode.STORE, OUTPUT_ADDRESS))
                elif row == Term.CR:
                    index = cr_machine(index, instructions)
                elif row in [Opcode.DUP, Opcode.DROP, Opcode.CLEAR]:
                    instructions.append(create_instruction(index, row, row))
                else:
                    if re.search("^(!|@)\\*?$", next(i, code)):
                        variable_pointer = check_variable(row, variables, variable_pointer)
                        if re.search(".\\*", next(i, code)):
                            opcode = Opcode.IND_STORE if next(i, code) == Term.IND_STORE else Opcode.IND_LOAD
                        else:
                            opcode = Opcode.STORE if next(i, code) == Term.STORE else Opcode.LOAD
                        instructions.append(create_instruction(index, next(i, code), opcode, variables[row]))
                        i += 1
                    else:
                        instructions.append(create_instruction(index, row, Opcode.CALL, procedures[row]))

                if instructions[0]["term"] == "start" and "arg" not in instructions[0] and not parse_procedures:
                    instructions[0]["arg"] = index
                index += 1
            i += 1
        if len(procedures) == 0 and parse_procedures:
            instructions.pop()
            index -= 1
        parse_procedures = False

    instructions.append(create_instruction(index, "stop", Opcode.STOP))
    return instructions


def main(source, target):
    with open(source, "r", encoding="utf-8") as file:
        code = file.read()
        code = code.strip()
        code = re.split("\\s+|\n", code)
        machine = translator(code)
    buf = []
    for instr in machine:
        buf.append(json.dumps(instr))
    with open(target, "w") as f:
        f.write("[" + ",\n ".join(buf) + "]")


if __name__ == '__main__':
    assert len(sys.argv) == 3, "Wrong arguments: translator.py <input_file> <target_file>"
    _, source, target = sys.argv
    main(source, target)

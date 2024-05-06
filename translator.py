import json
import sys
import re
from processor.isa import Opcode

INPUT_ADDRESS = 0
OUTPUT_ADDRESS = 1


def parse_math(row):
    return {
        "+": Opcode.ADD,
        "-": Opcode.SUB,
        "*": Opcode.MUL,
        "/": Opcode.DIV,
        "++": Opcode.INC,
        "--": Opcode.DEC,
        ">": Opcode.GREATER,
        "<": Opcode.LESS,
        "=": Opcode.EQUAL,
        "!=": Opcode.NOT_EQUAL
    }.get(row)


def create_instruction(index, term, opcode, arg=None):
    instr = {"index": index, "term": term, "opcode": opcode}
    if arg is not None:
        instr["arg"] = arg
    return instr


def inverse_condition(opcode):
    return {
        Opcode.EQUAL: Opcode.NOT_EQUAL,
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
            if char != '"':
                index = store_char(instructions, index, char)
        if row[-1] == '"':
            stop = i
            break
        else:
            index = store_char(instructions, index, " ")
    instructions.append(create_instruction(index, None, Opcode.DROP))
    return stop, index + 1


def insert_procedure(instructions, procedures, index):
    for i, instr in enumerate(procedures):
        new_instr = instr.copy()
        new_instr["index"] = index + i
        instructions.append(new_instr)
    return instructions[-1]["index"] + 1


def cr_machine(index, instructions):
    instructions.extend((create_instruction(index, "cr", Opcode.PUSH, 10),
                        create_instruction(index + 1, "cr", Opcode.STORE, OUTPUT_ADDRESS),
                        create_instruction(index + 2, "cr", Opcode.DROP)))
    return index + 2


def check_variable(row, variables, variable_pointer):
    if row not in variables:
        variables[row] = variable_pointer
        variable_pointer += 1
    return variable_pointer


def indirect(index, addr, opcode):
    term = "!*" if opcode == Opcode.IND_STORE else "@*"
    return index + 3, (create_instruction(index, term, Opcode.DUP),
                       create_instruction(index + 1, term, opcode, addr),
                       create_instruction(index + 2, term, Opcode.DROP))


def translator(code):
    instructions = []
    index, i = 0, 0
    jump_buf = []

    procedures = {}
    cur_procedure, proc_declare_start = None, None

    variables = {}
    variable_pointer = 2

    while i < len(code):
        row = code[i]
        if '"' in row:
            i, index = parse_string(instructions, code, index, i)
        elif row == ";":
            instructions[jump_buf.pop()]["arg"] = index
        elif row == "begin":
            jump_buf.append(index)
        elif row == ":":
            if cur_procedure is None:
                cur_procedure = code[i + 1]
                procedures[code[i + 1]] = []
                i += 1
                proc_declare_start = index
            else:
                procedures[cur_procedure] = instructions[proc_declare_start:]
                instructions = instructions[:proc_declare_start]
                index = proc_declare_start
                cur_procedure = None
        elif re.search("(!|@)\\*", code[i+1]):
            variable_pointer = check_variable(row, variables, variable_pointer)
            index, insert = indirect(index, variables[row], Opcode.IND_STORE if code[i+1] == "!*" else Opcode.IND_LOAD)
            instructions.extend(insert)
            i += 1
        elif row in procedures:
            index = insert_procedure(instructions, procedures[row], index)

        else:
            if row == "if":
                jump_buf.append(index)
                instructions[index - 1]["opcode"] = inverse_condition(instructions[index - 1]["opcode"])
                instructions.append(create_instruction(index, "if", Opcode.JIF))
            elif row == "else":
                label = jump_buf.pop()
                jump_buf.append(index)
                instructions.append(create_instruction(index, "else", Opcode.JMP))
                instructions[label]["arg"] = index + 1
            elif row == "until":
                instructions.append(create_instruction(index, "until", Opcode.JMP, jump_buf.pop()))

            elif re.search("-?[0-9]", row):
                instructions.append(create_instruction(index, row, Opcode.PUSH, int(row)))
            elif parse_math(row) is not None:
                instructions.append(create_instruction(index, row, parse_math(row)))
            elif re.search("!|@", code[i+1]):
                variable_pointer = check_variable(row, variables, variable_pointer)
                opcode = Opcode.STORE if code[i+1] == "!" else Opcode.LOAD
                instructions.append(create_instruction(index, code[i+1], opcode, variables[row]))
                i += 1

            elif row == "key":
                instructions.append(create_instruction(index, "key", Opcode.LOAD, INPUT_ADDRESS))
            elif row == "emit":
                instructions.append(create_instruction(index, "emit", Opcode.STORE, OUTPUT_ADDRESS))
            elif row == "cr":
                index = cr_machine(index, instructions)
            elif row in [Opcode.DUP, Opcode.DROP]:
                instructions.append(create_instruction(index, row, row))
            else:
                i += 1
                continue

            index += 1
        i += 1
    instructions.append(create_instruction(index, None, Opcode.STOP))
    return instructions


def main(code, target):
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

    with open(source, "r", encoding="utf-8") as file:
        code = file.read()
        main(code, target)

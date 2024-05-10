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


def insert_procedure(instructions, procedures, index):
    for i, instr in enumerate(procedures):
        new_instr = instr.copy()
        new_instr["index"] = index + i
        instructions.append(new_instr)
    return instructions[-1]["index"] + 1


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
        return code[i+1]
    except IndexError:
        return ""


def translator(code):
    instructions = []
    index, i = 0, 0
    jump_buf = []

    procedures = {}
    cur_procedure, proc_declare_start = None, None

    variables = {}
    variable_pointer = 2

    while i < len(code):
        if code[i] == Term.CLEAR:
            pass
        row = code[i]
        if Term.STRING in row:
            i, index = parse_string(instructions, code, index, i)
        elif row == Term.END_IF:
            instructions[jump_buf.pop()]["arg"] = index
        elif row == Term.BEGIN:
            jump_buf.append(index)
        elif row == Term.PROCEDURE:
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
        elif row in procedures:
            index = insert_procedure(instructions, procedures[row], index)

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

            elif re.search("^-?[0-9]*$", row):
                instructions.append(create_instruction(index, row, Opcode.PUSH, int(row)))
            elif parse_math(row) is not None:
                instructions.append(create_instruction(index, row, parse_math(row)))
            elif re.search("^(!|@)\\*?$", next(i, code)):
                variable_pointer = check_variable(row, variables, variable_pointer)
                if re.search(".\\*", next(i, code)):
                    opcode = Opcode.IND_STORE if next(i, code) == Term.IND_STORE else Opcode.IND_LOAD
                else:
                    opcode = Opcode.STORE if next(i, code) == Term.STORE else Opcode.LOAD
                instructions.append(create_instruction(index, next(i, code), opcode, variables[row]))
                i += 1

            elif row == Term.KEY:
                instructions.append(create_instruction(index, Term.KEY, Opcode.LOAD, INPUT_ADDRESS))
            elif row == Term.EMIT:
                instructions.append(create_instruction(index, Term.EMIT, Opcode.STORE, OUTPUT_ADDRESS))
            elif row == Term.CR:
                index = cr_machine(index, instructions)
            elif row in [Opcode.DUP, Opcode.DROP, Opcode.CLEAR]:
                instructions.append(create_instruction(index, row, row))
            else:
                i += 1
                continue

            index += 1
        i += 1
    instructions.append(create_instruction(index, None, Opcode.STOP))
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

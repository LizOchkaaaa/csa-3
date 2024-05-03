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
    }.get(row)


def jumps(operator):
    return {
        ">": Opcode.JLE,
        "<": Opcode.JGE,
        "=": Opcode.JNE
    }.get(operator)


def create_emit_machine(instructions, index, char):
    instructions.append({"index": index, "opcode": Opcode.TOP, "arg": ord(char)})
    instructions.append({"index": index + 1, "opcode": Opcode.STORE, "arg": OUTPUT_ADDRESS})
    return index + 2


def parse_string(instructions, code, index, start):
    instructions.append({"index": index, "opcode": Opcode.DUP, "arg": None})
    index += 1
    stop = 0
    code[start] = code[start].replace(".", "", 1)
    for i in range(start, len(code)):
        row = code[i]
        for char in row:
            if char != '"':
                index = create_emit_machine(instructions, index, char)
        if row[-1] == '"':
            stop = i
            break
        else:
            index = create_emit_machine(instructions, index, " ")
    instructions.append({"index": index, "opcode": Opcode.DROP, "arg": None})
    return stop, index + 1


def insert_procedure(instructions, procedures, index):
    for i, instr in enumerate(procedures):
        new_instr = instr.copy()
        new_instr["index"] = index + i
        instructions.append(new_instr)
    return instructions[-1]["index"] + 1


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
                cur_procedure = code[i+1]
                procedures[code[i+1]] = []
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
            instr = {"index": index, "arg": None}
            if row == "if":
                jump_buf.append(index)
                instr["opcode"] = jumps(code[i-1])
            elif row == "else":
                instr["opcode"] = Opcode.JMP
                label = jump_buf.pop()
                jump_buf.append(index)
                instructions[label]["arg"] = index + 1
            elif row == "until":
                instr["opcode"] = jumps(code[i-1])
                instr["arg"] = jump_buf.pop()
            elif re.search("-?[0-9]", row):
                instr["opcode"] = "push"
                instr["arg"] = int(row)
            elif parse_math(row) is not None:
                instr["opcode"] = parse_math(row)
            elif code[i+1] == "!":
                if row not in variables:
                    variables[row] = variable_pointer
                    variable_pointer += 1
                instr["opcode"] = Opcode.LOAD
                instr["arg"] = variables[row]
                i += 1
            elif code[i+1] == "@":
                instr["opcode"] = Opcode.STORE
                instr["arg"] = variables[row]
                i += 1
            elif row in [Opcode.DUP, Opcode.DROP]:
                instr["opcode"] = row

            instructions.append(instr)

            index += 1
        i += 1
    instructions.append({"index": index, "opcode": Opcode.STOP})
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

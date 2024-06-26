import json
import logging
import sys
from processor.machine import DataPath, ControlUnit


def main(code_file, input_file):
    logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")
    with open(code_file, "r") as file:
        instructions = json.load(file)
    with open(input_file, "r") as file:
        input_tokens = file.readline()
        input_tokens = list(input_tokens)
        input_tokens.append("\x00")

    data_path = DataPath(30, input_tokens)
    control_unit = ControlUnit(instructions, data_path)
    out, ticks, instr_count = control_unit.start()

    if len(out) > 0:
        print(out, "\n-------------------------------")
    print(f"Количество инструкций: {instr_count}")
    print(f"Количество тактов: {ticks}")


if __name__ == "__main__":
    assert len(sys.argv) == 3, "Wrong arguments: machine.py <code_file> <input_file>"
    _, code_file, input_file = sys.argv
    main(code_file, input_file)

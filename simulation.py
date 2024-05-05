import itertools
import json
import sys
from processor.machine import DataPath, ControlUnit


def main(code_file, input_file):
    with open(code_file) as file:
        instructions = json.load(file)
    with open(input_file) as file:
        input_tokens = file.readline()
        input_tokens = list(input_tokens)

    data_path = DataPath(30, input_tokens)
    control_unit = ControlUnit(instructions, data_path)
    out, ticks = control_unit.start()

    if len(out) > 0:
        print(out, "\n-------------------------------")
    print(f"Количество инструкций: {len(instructions)}")
    print(f"Количество тактов: {ticks}")


if __name__ == "__main__":
    assert len(sys.argv) == 3, "Wrong arguments: machine.py <code_file> <input_file>"
    _, code_file, input_file = sys.argv
    main(code_file, input_file)

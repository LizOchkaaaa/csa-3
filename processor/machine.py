from processor.isa import Opcode
from processor.microcode import Microcode
from processor.signals import Signals
import logging

INPUT_ADDRESS = 0
OUTPUT_ADDRESS = 1


class DataPath:

    def __init__(self, size, input_tokens):
        self.data_stack = []
        self.tos = 0
        self.address_reg = 0
        self.data_memory = [0] * size
        self.data_memory_out = 0
        self.alu_out = 0
        self.arg_tos = 0
        self.arg_address = 0
        self.pc = 0

        self.input_tokens = input_tokens
        self.output_buffer = []

        self.term = None

    def signal_latch_tos(self, signal):
        buses = {
            Signals.LATCH_TOS_ARG: self.arg_tos,
            Signals.LATCH_TOS_MEM_OUT: self.data_memory_out,
            Signals.LATCH_TOS_FROM_ALU: self.alu_out,
            Signals.LATCH_TOS_FROM_STACK: self.data_stack[-1] if self.data_stack != [] else 0,
            Signals.LATCH_TOS_FROM_PC: self.pc
        }
        self.tos = buses[signal]

    def signal_latch_address(self, signal):
        self.address_reg = self.arg_address if signal == Signals.LATCH_ADDR_ARG else self.data_memory_out

    def signal_stack_push(self):
        self.data_stack.append(self.tos)

    def signal_stack_pop(self):
        self.data_stack.pop() if self.data_stack != [] else None

    def signal_stack_clear(self):
        self.data_stack.clear()

    def memory_read(self):
        if self.address_reg == INPUT_ADDRESS:
            char = self.input_tokens.pop(0)
            self.data_memory[self.address_reg] = ord(char)
            logging.info(f"add char '{char}' from input buffer")
        self.data_memory_out = self.data_memory[self.address_reg]

    def memory_write(self):
        self.data_memory[self.address_reg] = self.tos
        if self.address_reg == OUTPUT_ADDRESS:
            if self.term == ".":
                num = self.data_memory[self.address_reg]
                logging.info(f"add number '{num}' to output buffer")
                self.output_buffer.append(str(num))
            else:
                char = chr(self.data_memory[self.address_reg])
                logging.info(f"add char '{char}' to output buffer")
                self.output_buffer.append(char)

    def alu(self, operation=Opcode.ADD, left_operand=0):
        self.alu_out = self.tos
        if operation in [Opcode.INC, Opcode.DEC]:
            self.alu_out = self.alu_out + 1 if operation == Opcode.INC else self.alu_out - 1
        elif left_operand != 0:
            oper = self.data_stack[-1] if self.data_stack != [] else 0
            operations = {
                Opcode.ADD: oper + self.tos,
                Opcode.SUB: oper - self.tos,
                Opcode.MUL: oper * self.tos,
                Opcode.DIV: oper / self.tos if self.tos != 0 else 0,
                Opcode.MOD: oper % self.tos if self.tos != 0 else 0,
                Opcode.LESS_EQ: oper <= self.tos,
                Opcode.GREATER: oper > self.tos,
                Opcode.EQUAL: oper == self.tos,
                Opcode.NOT_EQUAL: oper != self.tos
            }
            self.alu_out = int(operations[operation])


class ControlUnit:

    def __init__(self, instructions, dp: DataPath):
        self._tick = 0
        self.instr_count = 1

        self.PC = 0
        self.mPC = 0
        self.mPC_address = 0
        self.stop = False
        self.instructions = instructions
        self.instr = instructions[0]
        self.dp = dp
        self.microcode = Microcode(self, dp)

    def tick(self):
        if self._tick < 1000:
            logging.debug(self)
            if self._tick == 999:
                logging.info("Cut log due to its size")
        self._tick += 1

    def translate_opcode_to_mc_address(self):
        self.mPC_address = Microcode.addresses[self.instr["opcode"]]

    def set_stop(self):
        self.stop = True

    def signal_latch_mPC(self, signal):
        signals = {
            Signals.mPC_NEXT: self.mPC + 1,
            Signals.mPC_ZERO: 0,
            Signals.mPC_INSTR_JUMP: self.mPC_address
        }
        self.mPC = signals[signal]

    def signal_latch_PC(self, sel_pc):
        if sel_pc == Signals.PC_NEXT:
            self.PC += 1
        elif sel_pc == Signals.PC_TOS:
            self.PC = self.dp.tos
        else:
            self.PC = self.instr["arg"] if self.dp.tos != 0 or sel_pc == Signals.PC_JUMP else self.PC + 1
        self.instr = self.instructions[self.PC]

        self.dp.term = self.instr["term"]
        self.dp.pc = self.PC
        self.dp.arg_tos = self.instr["arg"] if "arg" in self.instr else 0
        self.dp.arg_address = self.instr["arg"] if "arg" in self.instr else 0
        self.instr_count += 1

    def start(self):
        while not self.stop:
            cur_mc = self.microcode.mc_memory[self.mPC]
            for signal in cur_mc:
                if isinstance(signal, tuple):
                    signal[0](*signal[1:])
                else:
                    signal()
            self.tick()

        return "".join(self.dp.output_buffer), self._tick, self.instr_count

    def __repr__(self):
        dp = self.dp
        return f"({self.instr['index']}: {self.instr['term']} -> {self.instr['opcode']} " \
               f"{self.instr['arg'] if 'arg' in self.instr else ''}) - " \
               f"TICK: {self._tick} - TOS: {dp.tos} - data stack: {dp.data_stack} - " \
               f"alu out: {dp.alu_out} - memory out: {dp.data_memory_out} - address reg: {dp.address_reg} - " \
               f"PC: {self.PC} - mPC: {self.mPC}"

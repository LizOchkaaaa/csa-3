from processor.isa import Opcode
from processor.microcode import Microcode
from processor.signals import Signals

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
        self.number_tos = 0
        self.number_address = 0

        self.input_tokens = input_tokens
        self.output_buffer = []

    def signal_latch_tos(self, signal):
        buses = {
            Signals.LATCH_TOS_NUMBER: self.number_tos,
            Signals.LATCH_TOS_MEM_OUT: self.data_memory_out,
            Signals.LATCH_TOS_FROM_ALU: self.alu_out,
            Signals.LATCH_TOS_FROM_STACK: self.data_stack[-1] if self.data_stack != [] else 0
        }
        self.tos = buses[signal]

    def signal_latch_address(self, signal):
        self.address_reg = self.number_address if signal == Signals.LATCH_ADDR_NUMBER else self.data_memory_out

    def signal_stack_push(self):
        self.data_stack.append(self.tos)

    def signal_stack_pop(self):
        self.data_stack.pop() if self.data_stack != [] else None

    def signal_stack_clear(self):
        self.data_stack.clear()

    def memory_read(self):
        if self.address_reg == INPUT_ADDRESS:
            self.data_memory[self.address_reg] = ord(self.input_tokens.pop(0))
        self.data_memory_out = self.data_memory[self.address_reg]

    def memory_write(self):
        self.data_memory[self.address_reg] = self.tos
        if self.address_reg == OUTPUT_ADDRESS:
            self.output_buffer.append(chr(self.data_memory[self.address_reg]))

    def alu(self, operation=Opcode.ADD, left_operand=0):
        self.alu_out = self.tos
        if operation in [Opcode.INC, Opcode.DEC]:
            self.alu_out = self.alu_out + 1 if operation == Opcode.INC else self.alu_out - 1
        elif left_operand != 0:
            oper = self.data_stack[-1] if self.data_stack != [] else 0
            operations = {
                Opcode.ADD: self.alu_out + oper,
                Opcode.SUB: self.alu_out - oper,
                Opcode.MUL: self.alu_out * oper,
                Opcode.DIV: self.alu_out / oper if oper != 0 else float('inf'),
                Opcode.GREATER: self.alu_out > self.data_stack[-1],
                Opcode.LESS: self.alu_out < self.data_stack[-1],
                Opcode.INC: self.alu_out + 1,
                Opcode.DEC: self.alu_out - 1,
                Opcode.EQUAL: self.alu_out == self.data_stack[-1],
                Opcode.NOT_EQUAL: self.alu_out != self.data_stack[-1]
            }
            self.alu_out = int(operations[operation])


class ControlUnit:

    def __init__(self, instructions, dp: DataPath):
        self._tick = 0
        self.PC = 0
        self.mPC = 0
        self.mPC_address = 0
        self.stop = False
        self.instructions = instructions
        self.instr = instructions[0]
        self.dp = dp
        self.microcode = Microcode(self, dp)

    def tick(self):
        self._tick += 1
        self.dp.number_tos = 0
        self.dp.number_address = 0

    def translate_opcode_to_mc_address(self):
        self.mPC_address = Microcode.addresses[self.instr["opcode"]]

    def set_stop(self):
        self.stop = True

    def set_number_in_tos(self):
        self.dp.number_tos = self.instr["arg"]

    def set_number_in_address(self):
        self.dp.number_address = self.instr["arg"]

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
        else:
            self.PC = self.instr["arg"] if self.dp.tos == 1 else self.PC + 1
        self.instr = self.instructions[self.PC]
        if self.instr["opcode"] == Opcode.IND_LOAD:
            pass

    def start(self):
        while not self.stop:
            cur_mc = self.microcode.mc_memory[self.mPC]
            for signal in cur_mc:
                if isinstance(signal, tuple):
                    signal[0](*signal[1:])
                else:
                    signal()
            self.tick()

        return "".join(self.dp.output_buffer), self._tick

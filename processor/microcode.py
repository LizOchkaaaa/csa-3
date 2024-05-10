from processor.signals import Signals
from processor.isa import Opcode


class Microcode:
    addresses = {
        Opcode.DUP: 1,
        Opcode.DROP: 3,
        Opcode.PUSH: 6,
        Opcode.TOP: 8,
        Opcode.CLEAR: 10,

        Opcode.LOAD: 12,
        Opcode.IND_LOAD: 15,
        Opcode.STORE: 20,
        Opcode.IND_STORE: 23,

        Opcode.ADD: 28,
        Opcode.SUB: 32,
        Opcode.MUL: 36,
        Opcode.DIV: 40,
        Opcode.MOD: 44,
        Opcode.LESS_EQ: 48,
        Opcode.GREATER: 52,
        Opcode.EQUAL: 56,
        Opcode.NOT_EQUAL: 60,
        Opcode.INC: 64,
        Opcode.DEC: 66,

        Opcode.JMP: 68,
        Opcode.JIF: 69,
        Opcode.STOP: 70
    }

    def math_operation(self, opcode, mPC_next, instr_end):
        return ([(self.dp.alu, opcode, Signals.OPERAND_STACK), mPC_next],
                [self.dp.signal_stack_push, mPC_next],
                [(self.dp.signal_latch_tos, Signals.LATCH_TOS_FROM_ALU), mPC_next],
                instr_end)

    def inc_dec(self, opcode, mPC_next, instr_end):
        return ([(self.dp.alu, opcode), (self.dp.signal_latch_tos, Signals.LATCH_TOS_FROM_ALU), mPC_next],
                instr_end)

    def indirect(self, mPC_next):
        return ([self.cu.set_number_in_address, (self.dp.signal_latch_address, Signals.LATCH_ADDR_NUMBER), mPC_next],
                [self.dp.memory_read, mPC_next],
                [(self.dp.signal_latch_address, Signals.LATCH_ADDR_FROM_MEM), mPC_next])

    def __init__(self, cu, dp):
        self.cu = cu
        self.dp = dp
        self.mPC = 0

        instr_end = [(cu.signal_latch_PC, Signals.PC_NEXT), (cu.signal_latch_mPC, Signals.mPC_ZERO)]
        mPC_next = (cu.signal_latch_mPC, Signals.mPC_NEXT)

        self.mc_memory = [
            [cu.translate_opcode_to_mc_address, (cu.signal_latch_mPC, Signals.mPC_INSTR_JUMP)],

            # dup
            [dp.signal_stack_push, mPC_next],
            instr_end,

            # drop
            [(dp.signal_latch_tos, Signals.LATCH_TOS_FROM_STACK), mPC_next],
            [dp.signal_stack_pop, mPC_next],
            instr_end,

            # push
            [dp.signal_stack_push, cu.set_number_in_tos, (dp.signal_latch_tos, Signals.LATCH_TOS_NUMBER), mPC_next],
            instr_end,

            # top
            [cu.set_number_in_tos, (dp.signal_latch_tos, Signals.LATCH_TOS_NUMBER), mPC_next],
            instr_end,

            # clear
            [dp.signal_stack_clear, mPC_next],
            instr_end,

            # load
            [cu.set_number_in_address, (dp.signal_latch_address, Signals.LATCH_ADDR_NUMBER), mPC_next],
            [dp.memory_read, dp.signal_stack_push, (dp.signal_latch_tos, Signals.LATCH_TOS_MEM_OUT), mPC_next],
            instr_end,

            # indirect load
            *self.indirect(mPC_next),
            [dp.memory_read, dp.signal_stack_push, (dp.signal_latch_tos, Signals.LATCH_TOS_MEM_OUT), mPC_next],
            instr_end,

            # store
            [cu.set_number_in_address, (dp.signal_latch_address, Signals.LATCH_ADDR_NUMBER), mPC_next],
            [dp.memory_write, mPC_next],
            instr_end,

            # indirect store
            *self.indirect(mPC_next),
            [dp.memory_write, mPC_next],
            instr_end,

            # math operations
            *self.math_operation(Opcode.ADD, mPC_next, instr_end),
            *self.math_operation(Opcode.SUB, mPC_next, instr_end),
            *self.math_operation(Opcode.MUL, mPC_next, instr_end),
            *self.math_operation(Opcode.DIV, mPC_next, instr_end),
            *self.math_operation(Opcode.MOD, mPC_next, instr_end),
            *self.math_operation(Opcode.LESS_EQ, mPC_next, instr_end),
            *self.math_operation(Opcode.GREATER, mPC_next, instr_end),
            *self.math_operation(Opcode.EQUAL, mPC_next, instr_end),
            *self.math_operation(Opcode.NOT_EQUAL, mPC_next, instr_end),

            # increment/decrement
            *self.inc_dec(Opcode.INC, mPC_next, instr_end),
            *self.inc_dec(Opcode.DEC, mPC_next, instr_end),

            # jmp
            [(cu.signal_latch_PC, Signals.PC_JUMP), (cu.signal_latch_mPC, Signals.mPC_ZERO)],
            # jif
            [(cu.signal_latch_PC, Signals.PC_JUMP_IF), (cu.signal_latch_mPC, Signals.mPC_ZERO)],

            # stop
            [cu.set_stop]
        ]

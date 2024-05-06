from processor.signals import Signals
from processor.isa import Opcode


class Microcode:

    addresses = {
        Opcode.DUP: 1,
        Opcode.DROP: 3,
        Opcode.PUSH: 6,
        Opcode.TOP: 9,
        Opcode.LOAD: 11,
        Opcode.STORE: 15,
        Opcode.EQUAL: 18,
        Opcode.NOT_EQUAL: 22,
        Opcode.JIF: 26,
        Opcode.STOP: 27
    }

    def math_operation(self, opcode, mPC_next, instr_end):
        return [(self.dp.alu, opcode, Signals.OPERAND_STACK), mPC_next], \
               [self.dp.signal_stack_push, mPC_next], \
               [(self.dp.signal_latch_tos, Signals.LATCH_TOS_FROM_ALU), mPC_next],\
               instr_end

    def inc_dec(self, opcode, mPC_next, instr_end):
        return [(self.dp.alu, opcode), (self.dp.signal_latch_tos, Signals.LATCH_TOS_FROM_ALU), mPC_next], \
               [instr_end]

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
            [(dp.signal_latch_tos, Signals.LATCH_TOS_FROM_STACK), dp.signal_stack_pop, mPC_next],
            [dp.signal_stack_pop, mPC_next],
            instr_end,

            # push
            [dp.signal_stack_push, cu.set_number_in_tos, mPC_next],
            [(dp.signal_latch_tos, Signals.LATCH_TOS_NUMBER), mPC_next],
            instr_end,

            # top
            [cu.set_number_in_tos, (dp.signal_latch_tos, Signals.LATCH_TOS_NUMBER), mPC_next],
            instr_end,

            # load
            [cu.set_number_in_address, (dp.signal_latch_address, Signals.LATCH_ADDR_NUMBER), mPC_next],
            [dp.memory_read, dp.signal_stack_push, mPC_next],
            [(dp.signal_latch_tos, Signals.LATCH_TOS_MEM_OUT), mPC_next],
            instr_end,

            # store
            [cu.set_number_in_address, (dp.signal_latch_address, Signals.LATCH_ADDR_NUMBER), mPC_next],
            [dp.memory_write, mPC_next],
            instr_end,

            # math operations
            *self.math_operation(Opcode.EQUAL, mPC_next, instr_end),
            *self.math_operation(Opcode.NOT_EQUAL, mPC_next, instr_end),

            # increment/decrement
            *self.inc_dec(Opcode.INC, mPC_next, instr_end),
            *self.inc_dec(Opcode.DEC, mPC_next, instr_end),

            # jne
            [(cu.signal_latch_PC, Signals.PC_JUMP), (cu.signal_latch_mPC, Signals.mPC_ZERO)],

            # stop
            [cu.set_stop]
        ]

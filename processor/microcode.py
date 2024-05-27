from processor.signals import Signals
from processor.isa import Opcode


class Microcode:
    addresses = {
        Opcode.DUP: 1,
        Opcode.DROP: 3,
        Opcode.PUSH: 6,
        Opcode.TOP: 9,
        Opcode.CLEAR: 11,

        Opcode.LOAD: 13,
        Opcode.IND_LOAD: 17,
        Opcode.STORE: 23,
        Opcode.IND_STORE: 26,

        Opcode.ADD: 31,
        Opcode.SUB: 35,
        Opcode.MUL: 39,
        Opcode.DIV: 43,
        Opcode.MOD: 47,
        Opcode.LESS_EQ: 51,
        Opcode.GREATER: 55,
        Opcode.EQUAL: 59,
        Opcode.NOT_EQUAL: 63,
        Opcode.INC: 67,
        Opcode.DEC: 69,

        Opcode.JMP: 71,
        Opcode.JIF: 72,

        Opcode.CALL: 73,
        Opcode.RET: 77,

        Opcode.STOP: 80
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
        return ([(self.dp.signal_latch_address, Signals.LATCH_ADDR_ARG), mPC_next],
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
            [dp.signal_stack_push, mPC_next],
            [(dp.signal_latch_tos, Signals.LATCH_TOS_ARG), mPC_next],
            instr_end,

            # top
            [(dp.signal_latch_tos, Signals.LATCH_TOS_ARG), mPC_next],
            instr_end,

            # clear
            [dp.signal_stack_clear, mPC_next],
            instr_end,

            # load
            [(dp.signal_latch_address, Signals.LATCH_ADDR_ARG), mPC_next],
            [dp.memory_read, dp.signal_stack_push, mPC_next],
            [(dp.signal_latch_tos, Signals.LATCH_TOS_MEM_OUT), mPC_next],
            instr_end,

            # indirect load
            *self.indirect(mPC_next),
            [dp.memory_read, dp.signal_stack_push, mPC_next],
            [(dp.signal_latch_tos, Signals.LATCH_TOS_MEM_OUT), mPC_next],
            instr_end,

            # store
            [(dp.signal_latch_address, Signals.LATCH_ADDR_ARG), mPC_next],
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

            # call
            [dp.signal_stack_push, mPC_next],
            [(dp.signal_latch_tos, Signals.LATCH_TOS_FROM_PC), mPC_next],
            [(dp.alu, Opcode.INC), (dp.signal_latch_tos, Signals.LATCH_TOS_FROM_ALU), mPC_next],
            [(cu.signal_latch_PC, Signals.PC_JUMP), (cu.signal_latch_mPC, Signals.mPC_ZERO)],

            # ret
            [(cu.signal_latch_PC, Signals.PC_TOS), mPC_next],
            [(dp.signal_latch_tos, Signals.LATCH_TOS_FROM_STACK), mPC_next],
            [dp.signal_stack_pop, (cu.signal_latch_mPC, Signals.mPC_ZERO)],

            # stop
            [cu.set_stop]
        ]

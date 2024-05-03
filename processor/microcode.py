from processor.signals import Signals


class Microcode:
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
            instr_end,

            # top
            [cu.set_number_in_tos, (dp.signal_latch_tos, Signals.LATCH_TOS_NUMBER), mPC_next],
            instr_end,

            # store
            [cu.set_number_in_address, (dp.signal_latch_address, Signals.LATCH_ADDR_NUMBER), mPC_next],
            [dp.memory_write, mPC_next],
            instr_end,

            # stop
            [cu.set_stop]
        ]

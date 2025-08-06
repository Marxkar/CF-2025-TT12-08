import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

@cocotb.test()
async def tb_jtag_tap(dut):
    clock = Clock(dut.clk, 20, units="ns")  # 20ns period = 50 MHz
    cocotb.start_soon(clock.start())

    dut.ena.value = 1  # Always enabled for JTAG TAP
    dut.ui_in.value = 0

    # Apply reset: hold low for 50ns
    dut.rst_n.value = 0
    await Timer(50, units="ns")
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)

    dut._log.info("Reset deasserted, starting JTAG TAP sequence.")

    # Sequence of JTAG TAP cycles (each item: (TMS, TDI))
    jtag_sequence = [
        (1, 0),  # test_logic_reset
        (1, 0),  # still in test_logic_reset
        (0, 0),  # run_idle
        (1, 0),  # select_dr_scan
        (1, 0),  # select_ir_scan
        (0, 0),  # capture_ir
        (0, 1),  # shift_ir - shift in bit '1'
        (0, 0),  # shift_ir - shift in bit '0'
        (1, 1),  # exit_1_ir with bit '1'
        (0, 0),  # pause_ir
        (1, 0),  # exit_2_ir
        (0, 0),  # update_ir
    ]

    # Run IR update sequence
    for idx, (tms, tdi) in enumerate(jtag_sequence):
        dut.ui_in.value = (tms << 1) | tdi
        await Timer(20, units="ns")  # one clock period (20ns)
        await RisingEdge(dut.clk)
        dut._log.info(f"[IR seq] Step {idx}: TMS={tms} TDI={tdi} uo_out={dut.uo_out.value}")

    # Run idle 5 cycles
    for i in range(5):
        dut.ui_in.value = 0
        await Timer(20, units="ns")
        await RisingEdge(dut.clk)
        dut._log.info(f"[Run idle] Cycle {i}")

    # Shift DR sequence
    jtag_dr_sequence = [
        (1, 0),  # select_dr_scan
        (0, 0),  # capture_dr
        (0, 1),  # shift_dr: bit '1'
        (0, 0),  # shift_dr: bit '0'
        (0, 1),  # shift_dr: bit '1'
        (1, 0),  # exit_1_dr
        (0, 0),  # pause_dr
        (1, 0),  # exit_2_dr
        (0, 0),  # update_dr
    ]

    for idx, (tms, tdi) in enumerate(jtag_dr_sequence):
        dut.ui_in.value = (tms << 1) | tdi
        await Timer(20, units="ns")
        await RisingEdge(dut.clk)
        dut._log.info(f"[DR seq] Step {idx}: TMS={tms} TDI={tdi} uo_out={dut.uo_out.value}")

    # Run idle 5 more cycles before finishing
    for i in range(5):
        dut.ui_in.value = 0
        await Timer(20, units="ns")
        await RisingEdge(dut.clk)
        dut._log.info(f"[Final idle] Cycle {i}")

    dut._log.info("TEST COMPLETE")

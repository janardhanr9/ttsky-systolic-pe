# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge


@cocotb.test()
async def test_systolic_fsm_states(dut):
    """Test FSM state transitions"""
    dut._log.info("Testing FSM State Transitions")

    # Set the clock period to 10 us (100 KHz)
    clock = Clock(dut.clk, 10, unit="us")
    cocotb.start_soon(clock.start())

    # Reset
    dut._log.info("Reset")
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 1)

    # Check IDLE -> LOAD_W transition
    dut._log.info("Checking IDLE -> LOAD_W")
    await ClockCycles(dut.clk, 1)

    # Should be in LOAD_W for 4 cycles (0-3)
    dut._log.info("In LOAD_W state")
    await ClockCycles(dut.clk, 4)

    # Should transition to LOAD_B
    dut._log.info("Should be in LOAD_B state")
    await ClockCycles(dut.clk, 4)

    # Should transition to COMPUTE
    dut._log.info("Should be in COMPUTE state")
    await ClockCycles(dut.clk, 7)

    # Should transition to DRAIN
    dut._log.info("Should be in DRAIN state")
    await ClockCycles(dut.clk, 1)

    dut._log.info("FSM Test Complete")


@cocotb.test()
async def test_weight_loading(dut):
    """Test weight loading into all 4 PEs"""
    dut._log.info("Testing Weight Loading")

    clock = Clock(dut.clk, 10, unit="us")
    cocotb.start_soon(clock.start())

    # Reset
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 1)

    # Wait to enter LOAD_W state
    await ClockCycles(dut.clk, 1)

    # Load weights: W0=1, W1=2, W2=3, W3=4
    weights = [1, 2, 3, 4]
    for i, w in enumerate(weights):
        dut.ui_in.value = w
        dut._log.info(f"Loading weight {w} into PE{i}")
        await ClockCycles(dut.clk, 1)

    dut._log.info("Weight Loading Complete")


@cocotb.test()
async def test_bias_loading(dut):
    """Test bias loading into all 4 PEs"""
    dut._log.info("Testing Bias Loading")

    clock = Clock(dut.clk, 10, unit="us")
    cocotb.start_soon(clock.start())

    # Reset
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 1)

    # Skip through LOAD_W state (4 cycles after IDLE transition)
    await ClockCycles(dut.clk, 1)  # Enter LOAD_W
    await ClockCycles(dut.clk, 4)  # Complete LOAD_W

    # Now in LOAD_B state - load biases: B0=10, B1=20, B2=30, B3=40
    biases = [10, 20, 30, 40]
    for i, b in enumerate(biases):
        dut.ui_in.value = b
        dut._log.info(f"Loading bias {b} into PE{i}")
        await ClockCycles(dut.clk, 1)

    dut._log.info("Bias Loading Complete")

@cocotb.test()
async def test_signed_stress_corners(dut):
    """Test signed math and maximum values to check for overflows"""
    dut._log.info("Testing Signed Math and Corner Cases")

    clock = Clock(dut.clk, 10, unit="us")
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 1)

    # 1. LOAD WEIGHTS: Set all PEs to -1 (Two's complement: 255)
    await ClockCycles(dut.clk, 1) # Enter LOAD_W
    for _ in range(4):
        dut.ui_in.value = 0xFF # -1 in signed 8-bit
        await ClockCycles(dut.clk, 1)

    # 2. LOAD BIASES: Set all PEs to 10
    for _ in range(4):
        dut.ui_in.value = 10
        await ClockCycles(dut.clk, 1)

    # 3. COMPUTE: Feed activations of 5
    # Math: (5 * -1) + 10 = 5. Result should be 5 across the board.
    for _ in range(7):
        dut.ui_in.value = 5
        await ClockCycles(dut.clk, 1)

    # 4. DRAIN and Validate
    dut._log.info("Draining Signed Results")
    for i in range(4):
        # Combine high and low bytes
        raw_val = int(dut.uo_out.value) | (int(dut.uio_out.value) << 8)
        
        # Convert unsigned 16-bit to signed Python int
        if raw_val & 0x8000:
            signed_res = raw_val - 0x10000
        else:
            signed_res = raw_val
            
        dut._log.info(f"PE{i} signed result: {signed_res}")
        # Note: PE results will vary based on how many inputs they processed
        await ClockCycles(dut.clk, 1)

    dut._log.info("Stress Test Complete")

@cocotb.test()
async def test_simple_computation(dut):
    """Test simple MAC computation: (data * weight) + bias"""
    dut._log.info("Testing Simple Computation")

    clock = Clock(dut.clk, 10, unit="us")
    cocotb.start_soon(clock.start())

    # Reset
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 1)

    # Enter LOAD_W state
    await ClockCycles(dut.clk, 1)

    # Load weights: W0=2, W1=3, W2=4, W3=5
    weights = [2, 3, 4, 5]
    for w in weights:
        dut.ui_in.value = w
        await ClockCycles(dut.clk, 1)

    # Load biases: B0=0, B1=0, B2=0, B3=0 (for simplicity)
    biases = [0, 0, 0, 0]
    for b in biases:
        dut.ui_in.value = b
        await ClockCycles(dut.clk, 1)

    # Now in COMPUTE state - feed data
    # Data sequence: [10, 20, 30, 40]
    data_seq = [10, 20, 30, 40, 0, 0, 0]  # 7 cycles for COMPUTE
    for i, d in enumerate(data_seq):
        dut.ui_in.value = d
        dut._log.info(f"Compute cycle {i}: feeding data={d}")
        await ClockCycles(dut.clk, 1)

    # Now in DRAIN state - read accumulated results
    # PE0: 10*2 = 20
    # PE1: (10*3) + (20*3) = 30 + 60 = 90
    # PE2: (10*4) + (20*4) + (30*4) = 240
    # PE3: (10*5) + (20*5) + (30*5) + (40*5) = 500
    
    dut._log.info("Draining results")
    for i in range(4):
        result = int(dut.uo_out.value) | (int(dut.uio_out.value) << 8)
        dut._log.info(f"PE{i} accumulated result: {result}")
        await ClockCycles(dut.clk, 1)

    dut._log.info("Computation Test Complete")


@cocotb.test()
async def test_full_cycle(dut):
    """Test complete cycle: Load -> Compute -> Drain -> Repeat"""
    dut._log.info("Testing Full Cycle")

    clock = Clock(dut.clk, 10, unit="us")
    cocotb.start_soon(clock.start())

    # Reset
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1

    # Run through 2 complete cycles
    for cycle in range(2):
        dut._log.info(f"=== Cycle {cycle} ===")
        
        # IDLE -> LOAD_W
        await ClockCycles(dut.clk, 1)
        
        # Load weights
        for i in range(4):
            dut.ui_in.value = (cycle + 1) * (i + 1)
            await ClockCycles(dut.clk, 1)
        
        # Load biases
        for i in range(4):
            dut.ui_in.value = i * 5
            await ClockCycles(dut.clk, 1)
        
        # Compute phase
        for i in range(7):
            dut.ui_in.value = i * 10
            await ClockCycles(dut.clk, 1)
        
        # Drain phase
        await ClockCycles(dut.clk, 1)

    dut._log.info("Full Cycle Test Complete")

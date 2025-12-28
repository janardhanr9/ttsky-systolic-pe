<!---

This file is used to generate your project datasheet. Please fill in the information below and delete any unused
sections.

You can also include images in this folder and reference them in the markdown. Each image must be less than
512 kb in size, and the combined size of all images must be less than 1 MB.
-->

## How it works

This project implements a **1D Systolic Array with 4 Processing Elements (PEs)** for multiply-accumulate (MAC) operations, optimized for the Tiny Tapeout Sky130 process. The design follows a weight-stationary architecture with deterministic timing and no handshaking.

### Architecture Overview

The systolic array consists of:

- **4 Processing Elements (PEs)** arranged in a 1D chain
- **Systolic Controller** managing the FSM and control signals
- **4-bit signed integer arithmetic** for inputs (weights, biases, activations)
- **8-bit signed accumulators** with saturation logic to prevent overflow

### Processing Element (PE) Design

Each PE contains:
- A 4-bit weight register (stationary, loaded once)
- An 8-bit accumulator with saturation logic for summing results
- Multiply-accumulate logic: `accumulator = saturate(accumulator + (data_in × weight))`
- Pass-through data path for chaining PEs
- Saturation range: -128 to 127 (8-bit signed)

### Systolic Data Flow

1. **Weight Loading**: Weights are loaded sequentially into each PE (W0, W1, W2, W3)
2. **Bias Loading**: Biases are loaded sequentially into each PE's accumulator (B0, B1, B2, B3)
3. **Compute Phase**: Activation data flows through the chain:
   - PE0 receives data on cycle 0, computes for 4 cycles
   - PE1 receives data on cycle 1, computes for 4 cycles
   - PE2 receives data on cycle 2, computes for 4 cycles
   - PE3 receives data on cycle 3, computes for 4 cycles
4. **Drain Phase**: Results are read out sequentially from each PE

### FSM States

The controller implements a 5-state FSM:
- **IDLE**: Initial state, transitions immediately to LOAD_W
- **LOAD_W**: Load weights (4 cycles, one per PE)
- **LOAD_B**: Load biases (4 cycles, one per PE)
- **COMPUTE**: MAC operations (7 cycles to fill pipeline and compute)
- **DRAIN**: Output accumulated results (1+ cycles to read results)

### I/O Interface

- **ui_in[3:0]**: 4-bit data input (weights during LOAD_W, biases during LOAD_B, activations during COMPUTE)
- **ui_in[7:4]**: Unused
- **uo_out[7:0]**: 8-bit signed result during DRAIN
- **uio_out[7:0]**: Unused (all zeros)
- **uio_oe[7:0]**: Bidirectional enable (always output = 0xFF)

## How to test

### Automated Testing

The design includes a comprehensive cocotb test suite with 6 test cases:

1. **FSM State Transitions**: Verifies the state machine progresses correctly through all states
2. **Weight Loading**: Confirms weights are loaded into all 4 PEs
3. **Bias Loading**: Confirms biases are loaded into all 4 PE accumulators
4. **Signed Math Stress Test**: Tests signed arithmetic and corner cases (negative weights, overflow handling)
5. **Simple Computation**: Validates MAC operations with known inputs/outputs
6. **Full Cycle Test**: Tests multiple complete cycles of operation

Run the tests:
```bash
cd test
make clean
make
```

View waveforms:
```bash
gtkwave tb.fst tb.gtkw
```

### Manual Testing Procedure

1. **Reset**: Assert `rst_n = 0` for at least 5 clock cycles, then release
2. **Load Weights**: The system automatically enters LOAD_W state. Apply 4 weight values on `ui_in[3:0]`, one per clock cycle (range: -8 to 7)
3. **Load Biases**: System transitions to LOAD_B. Apply 4 bias values on `ui_in[3:0]`, one per clock cycle (range: -8 to 7)
4. **Compute**: System transitions to COMPUTE. Apply 7 activation values on `ui_in[3:0]` (first 4 are processed, remaining 3 are for pipeline flushing)
5. **Drain**: System transitions to DRAIN. Read results from `uo_out[7:0]` (8-bit signed values with saturation, range: -128 to 127):
   - Cycle 0: PE0 result (sum of 4 MAC operations, saturated)
   - Cycle 1: PE1 result
   - Cycle 2: PE2 result
   - Cycle 3: PE3 result

### Example Test Case

Load: W = [2, 3, 4, 5], B = [0, 0, 0, 0]
Compute: Data = [7, 7, 7, 7, 0, 0, 0] (max 4-bit signed value)

Expected results (with saturation):
- PE0: 7×2 + 7×2 + 7×2 + 7×2 = 56
- PE1: 7×3 + 7×3 + 7×3 + 7×3 = 84
- PE2: 7×4 + 7×4 + 7×4 + 7×4 = 112
- PE3: 7×5 + 7×5 + 7×5 + 7×5 = 140 → **saturated to 127**

Note: Results exceeding ±127 will be saturated to the 8-bit signed range.

### Timing Constraints

- Clock frequency: 50 MHz (20ns period)
- Total cycle count per operation: 16 cycles (1 IDLE + 4 LOAD_W + 4 LOAD_B + 7 COMPUTE + 1 DRAIN minimum)
- Deterministic latency: No stalls or variable timing

## External hardware

No external hardware is required. The design is fully self-contained and can be tested using:
- Clock source (50 MHz recommended)
- 4-bit data input bus (ui_in[3:0])
- 8-bit result output bus (uo_out[7:0])

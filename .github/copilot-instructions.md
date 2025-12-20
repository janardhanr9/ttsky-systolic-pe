# Tiny Tapeout Vector ALU Project

## Architecture Overview

This is a **Tiny Tapeout** project for creating a **vector ALU** (Arithmetic Logic Unit) design synthesized onto real silicon ASICs. The design flow:
1. SystemVerilog source in [src/](../src/) → RTL simulation → Gate-level synthesis → ASIC fabrication via LibreLane
2. GitHub Actions automatically build GDS files for chip fabrication
3. All designs use the standardized `tt_um_*` top module interface with fixed I/O ports

**Key constraints**: 
- Targets ~167x108 µM silicon tiles (1x1 default, expandable to 8x2)
- 8-bit I/O buses: `ui_in[7:0]`, `uo_out[7:0]`, `uio_in/out[7:0]` (bidirectional)
- **Use SystemVerilog** (`.sv` extension) for modern features like `logic`, `always_ff`, `always_comb`

**Vector ALU Design Considerations**:
- With 8-bit I/O, consider serial/pipelined vector element processing
- Define vector width, element size, and supported operations early
- Use `uio_*` bidirectional pins for operand input or result output expansion
- Clock domain: Single clock (`clk`), active-low async reset (`rst_n`)

## Critical Module Interface

All designs **must** use this exact top module signature. Use **SystemVerilog syntax** (`.sv` files):

```systemverilog
module tt_um_<your_unique_name> (
    input  logic [7:0] ui_in,    // Dedicated 8-bit input
    output logic [7:0] uo_out,   // Dedicated 8-bit output
    input  logic [7:0] uio_in,   // Bidirectional I/O: input path
    output logic [7:0] uio_out,  // Bidirectional I/O: output path
    output logic [7:0] uio_oe,   // Bidirectional I/O: enable (0=input, 1=output)
    input  logic       ena,      // Always 1 when powered
    input  logic       clk,      // Clock input
    input  logic       rst_n     // Active-low reset
);
```

**Rules**:
- Top module name must start with `tt_um_` followed by your GitHub username for uniqueness
- Use `logic` type instead of `wire`/`reg` (SystemVerilog best practice)
- All outputs must be assigned (use `assign uio_oe = 8'b0;` if unused)
- Suppress warnings for unused inputs: `logic _unused = &{ena, 1'b0};`
- Use `always_ff` for sequential logic, `always_comb` for combinational

## Configuration Workflow

When modifying the design, update **both** locations (they must stay synchronized):

1. **[info.yaml](../info.yaml)**: Project metadata for Tiny Tapeout submission
   - `top_module`: Must match your SystemVerilog module name exactly
   - `source_files`: List all `.sv` (or `.v`) files under `src/`
   - `language`: Set to `"SystemVerilog"` for `.sv` files
   - `pinout`: Document signal names for each I/O pin (for datasheet generation)

2. **[test/Makefile](../test/Makefile)**: 
   - `PROJECT_SOURCES`: Must match `source_files` in `info.yaml`
   - Update when adding/removing source files

3. **[test/tb.v](../test/tb.v)**: 
   - Replace `tt_um_example` with your actual module name

## Testing Workflow

Uses **cocotb** (Python-based HDL verification) + Icarus Verilog simulator.

### RTL Simulation (default):
```bash
cd test
make -B
```

### Gate-Level Simulation (post-synthesis):
```bash
cd test
make -B GATES=yes
```
Requires copying synthesized netlist to `test/gate_level_netlist.v` first.

### Waveform Viewing:
```bash
gtkwave tb.fst tb.gtkw    # or: surfer tb.fst
```
Default format is FST (compressed). For VCD: edit `tb.v` to use `$dumpfile("tb.vcd");` and run `make -B FST=`.

### Test Development:
- Edit [test/test.py](../test/test.py) to add cocotb test cases
- Access DUT signals via `dut.ui_in.value`, `dut.uo_out.value`, etc.
- Use `await ClockCycles(dut.clk, N)` to advance simulation time

## ASIC Synthesis Configuration

[src/config.json](../src/config.json) controls LibreLane ASIC toolchain settings:

**Common adjustments**:
- `PL_TARGET_DENSITY_PCT` (default: 60): Increase to 70-80 if placement fails with `GPL-0302` error
- `CLOCK_PERIOD` (default: 20ns = 50MHz): Increase if getting setup time violations
- `PL_RESIZER_HOLD_SLACK_MARGIN`: Increase if hold violations occur

**Do not modify** below the "DO NOT CHANGE" line unless you understand OpenLane flow implications.

## Project-Specific Conventions

- **SystemVerilog features**: Use `logic` instead of `wire`/`reg`, `always_ff` for sequential, `always_comb` for combinational
- **Default nettype**: Use `` `default_nettype none `` to catch typos (no implicit wire declarations)
- **Timescale**: Testbenches use `` `timescale 1ns / 1ps ``
- **SPDX headers**: Include copyright/license at top of files (Apache-2.0 for TT projects)
- **Documentation**: [docs/info.md](../docs/info.md) auto-generates the project datasheet on tinytapeout.com

## Vector ALU Implementation Tips

- **Serial processing**: With 8-bit I/O, implement operations on vector elements sequentially across multiple clock cycles
- **Control interface**: Reserve some `ui_in` bits for operation selection (e.g., ADD, SUB, MUL, shift, etc.)
- **State machine**: Use an FSM to manage multi-cycle vector operations (IDLE → LOAD → COMPUTE → OUTPUT)
- **Register file**: Store vector operands in internal registers; use `uio_in`/`uio_out` for data transfer
- **Example protocol**: `ui_in[2:0]` = opcode, `ui_in[7:3]` = control flags, then stream data via `uio_in`

## Quick Start Checklist

1. Rename `src/project.v` to `src/project.sv` and update module name to `tt_um_<yourusername>_vector_alu`
2. Update `info.yaml`: title, author, description, top_module, language = "SystemVerilog", source_files = ["project.sv"], pinout labels
3. Implement vector ALU logic in [src/project.sv](../src/project.sv) using SystemVerilog syntax
4. Update [test/Makefile](../test/Makefile) `PROJECT_SOURCES` to `project.sv`
5. Write tests in [test/test.py](../test/test.py) and update [test/tb.v](../test/tb.v) module name
6. Run `cd test && make -B` to verify RTL simulation passes
7. Document in [docs/info.md](../docs/info.md): how it works, how to test, external hardware needs

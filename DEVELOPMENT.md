# Tiny Tapeout SystemVerilog Development Guide

Complete reference for working with this Tiny Tapeout project independently.

## Project Structure

```
.
├── src/
│   ├── project.sv          # Your main SystemVerilog design file
│   └── config.json         # OpenLane ASIC synthesis configuration
├── test/
│   ├── test.py             # Cocotb Python testbench
│   ├── tb.v                # Verilog testbench wrapper
│   ├── Makefile            # Test build configuration
│   └── tb.gtkw             # GTKWave waveform viewer layout
├── docs/
│   └── info.md             # Project documentation (auto-generates datasheet)
├── info.yaml               # Project metadata for Tiny Tapeout
└── .github/
    └── copilot-instructions.md  # AI agent guidance
```

## SystemVerilog Compilation

### Compiler: Icarus Verilog

The project uses **Icarus Verilog** with SystemVerilog support:

```bash
iverilog -o sim.vvp -s tb -g2012 -I../src project.sv tb.v
```

**Key flags:**
- `-g2012`: Enable SystemVerilog/Verilog-2012 features (`logic`, `always_ff`, `always_comb`, etc.)
- `-s tb`: Set top-level module to `tb`
- `-I../src`: Include path for design files
- `-o sim.vvp`: Output compiled simulation file

### SystemVerilog Features Supported

- `logic` type instead of `wire`/`reg`
- `always_ff` for sequential logic
- `always_comb` for combinational logic
- `typedef enum` for state machines
- Array types: `logic [7:0] mem [0:15]`
- For loops with `int` variables

## Linting

### Verilator Lint (via OpenLane)

Linting is configured in `src/config.json`:

```json
"RUN_LINTER": 1,
"LINTER_INCLUDE_PDK_MODELS": 1
```

Linting runs automatically during GitHub Actions synthesis. To manually check locally (requires OpenLane setup):

```bash
# Install OpenLane/LibreLane first
# Then from project root:
docker run --rm -v $(pwd):/work -w /work efabless/openlane:latest \
  flow.tcl -design . -tag test -overwrite
```

**Common lint warnings to avoid:**
- Unused signals (use `logic _unused = &{signal, 1'b0};`)
- Undriven outputs (assign all outputs)
- Implicit wire declarations (use `` `default_nettype none ``)
- Width mismatches in assignments

## Testing Workflow

### Prerequisites

Tests use **cocotb** (Python-based HDL verification) + Icarus Verilog:

```bash
# Install via oss-cad-suite (includes both)
# Or install separately:
pip install cocotb pytest

# Verify installation
iverilog -V
python -c "import cocotb; print(cocotb.__version__)"
```

### Running Tests

**From test directory:**

```bash
cd test
make -B          # Build and run all tests
```

**What happens:**
1. `make` reads `Makefile` and `test.py`
2. Compiles SystemVerilog files via `iverilog -g2012`
3. Runs `vvp` simulator with cocotb
4. Executes all `@cocotb.test()` functions in `test.py`
5. Generates waveform file `tb.fst`
6. Exits with code 0 (pass) or non-zero (fail)

### Makefile Configuration

**Key variables in `test/Makefile`:**

```makefile
SIM = icarus                    # Simulator to use
FST = -fst                      # Waveform format (FST or VCD)
TOPLEVEL_LANG = verilog         # Keep as 'verilog' even for SV
PROJECT_SOURCES = project.sv    # Must match info.yaml source_files
COCOTB_TEST_MODULES = test      # Python test file (test.py)
```

**Must update when:**
- Adding/removing source files → update `PROJECT_SOURCES`
- Changing module name → update `TOPLEVEL` in `tb.v`

### Writing Tests in Python

**Basic test structure (`test/test.py`):**

```python
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles

@cocotb.test()
async def test_my_feature(dut):
    # Setup clock
    clock = Clock(dut.clk, 20, unit="ns")  # 50 MHz
    cocotb.start_soon(clock.start())
    
    # Reset sequence
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    
    # Test logic
    dut.ui_in.value = 42
    await ClockCycles(dut.clk, 1)
    
    assert dut.uo_out.value == 42, f"Expected 42, got {dut.uo_out.value}"
```

**Accessing signals:**
- Inputs: `dut.ui_in.value = 10`
- Outputs: `result = dut.uo_out.value.integer`
- Bit indexing: `dut.uo_out.value[7]`
- Logging: `dut._log.info("Message")`

### Viewing Waveforms

**FST format (default, smaller files):**

```bash
cd test
gtkwave tb.fst tb.gtkw         # Open with GTKWave
# or
surfer tb.fst                  # Open with Surfer (if installed)
```

**VCD format (slower, larger):**

1. Edit `test/tb.v`:
   ```verilog
   $dumpfile("tb.vcd");  // Change from tb.fst
   ```

2. Run without FST flag:
   ```bash
   make -B FST=
   ```

### Gate-Level Simulation

Test synthesized netlist (post-synthesis verification):

1. Run ASIC synthesis (via GitHub Actions or local OpenLane)
2. Copy gate-level netlist:
   ```bash
   cp runs/wokwi/results/final/verilog/gl/tt_um_*.v test/gate_level_netlist.v
   ```

3. Run gate-level tests:
   ```bash
   cd test
   make -B GATES=yes
   ```

This simulates with actual standard cells (slower but more accurate).

## Configuration Files

### info.yaml

**Must stay synchronized with code:**

```yaml
language: "SystemVerilog"      # For .sv files
top_module: "tt_um_example"    # Must match module name in project.sv
source_files:
  - "project.sv"                # Must match PROJECT_SOURCES in Makefile
```

**Update when:**
- Changing module name → update `top_module` AND `tb.v`
- Adding source files → update both `source_files` and `Makefile`
- Changing I/O usage → update `pinout` section

### src/config.json

**OpenLane ASIC synthesis settings. Common adjustments:**

```json
{
  "PL_TARGET_DENSITY_PCT": 60,      // Increase to 70-80 if placement fails
  "CLOCK_PERIOD": 20,               // ns (50 MHz). Increase if timing fails
  "PL_RESIZER_HOLD_SLACK_MARGIN": 0.1,  // Increase for hold violations
  "RUN_LINTER": 1                   // Enable Verilator linting
}
```

**Errors and fixes:**
- `GPL-0302` placement error → increase `PL_TARGET_DENSITY_PCT`
- Setup time violation → increase `CLOCK_PERIOD`
- Hold time violation → increase slack margins

## Essential Commands Cheatsheet

### Testing
```bash
cd test && make -B                    # Run RTL tests
cd test && make -B GATES=yes          # Run gate-level tests
cd test && make clean                 # Clean build artifacts
gtkwave test/tb.fst test/tb.gtkw     # View waveforms
```

### File Operations
```bash
mv src/project.v src/project.sv      # Convert to SystemVerilog
```

### Checking Status
```bash
grep "top_module" info.yaml           # Check module name
grep "PROJECT_SOURCES" test/Makefile  # Check sources
iverilog -g2012 src/project.sv        # Syntax check only
```

### Git Workflow
```bash
git add src/ test/ info.yaml docs/   # Stage changes
git commit -m "Implement feature X"  # Commit
git push                             # Triggers GitHub Actions build
```

## Module Interface Requirements

**All designs must use this exact signature:**

```systemverilog
module tt_um_<username>_<projectname> (
    input  logic [7:0] ui_in,      // Dedicated inputs
    output logic [7:0] uo_out,     // Dedicated outputs
    input  logic [7:0] uio_in,     // Bidirectional: input path
    output logic [7:0] uio_out,    // Bidirectional: output path
    output logic [7:0] uio_oe,     // Bidirectional: output enable
    input  logic       ena,        // Power enable (always 1)
    input  logic       clk,        // Clock
    input  logic       rst_n       // Active-low reset
);
```

**Critical rules:**
1. Module name must start with `tt_um_`
2. All 8 outputs must be assigned (use `8'b0` if unused)
3. Bidirectional pins: `uio_oe=0` for input, `uio_oe=1` for output
4. Suppress unused signal warnings:
   ```systemverilog
   logic _unused = &{ena, 1'b0};
   ```

## Common Issues & Solutions

### Test fails with "Module not found"
- Check `top_module` in `info.yaml` matches module name in `project.sv`
- Check `tt_um_example` in `test/tb.v` matches your module name

### Synthesis fails with placement error
- Increase `PL_TARGET_DENSITY_PCT` in `src/config.json` (try 70-80)
- Reduce design complexity or clock frequency

### "Width mismatch" warnings
- Explicitly specify widths: `8'b0` not just `0`
- Match signal widths in assignments

### Tests hang/timeout
- Check for combinational loops
- Verify reset logic properly initializes state
- Ensure clock is running: `cocotb.start_soon(clock.start())`

### "Unknown wire" errors
- Add `` `default_nettype none `` at top of file
- Declare all signals before use

## ASIC Build Pipeline

**Automatic via GitHub Actions:**

1. Push code → Triggers `.github/workflows/` actions
2. OpenLane synthesizes design to GDS
3. Results published to GitHub Pages
4. Check build status badges in README

**What gets built:**
- `GDS` file: Physical chip layout
- `LEF` file: Abstract layout view
- Gate-level netlist for verification
- Timing reports
- DRC/LVS check results

**Build artifacts location:**
- GitHub Pages: `https://<username>.github.io/<repo>/`
- Or download from Actions tab

## Development Workflow

**Typical iteration cycle:**

1. **Edit design:** Modify `src/project.sv`
2. **Update config:** Sync `info.yaml` if needed
3. **Test locally:** `cd test && make -B`
4. **Check waveforms:** `gtkwave tb.fst` if tests fail
5. **Fix and repeat:** Until tests pass
6. **Update docs:** Edit `docs/info.md`
7. **Commit & push:** Triggers ASIC synthesis
8. **Check Actions:** Monitor build on GitHub

## Resources

**Documentation:**
- Tiny Tapeout: https://tinytapeout.com
- SystemVerilog: https://www.chipverify.com/systemverilog/systemverilog-tutorial
- Cocotb: https://docs.cocotb.org/
- Icarus Verilog: https://steveicarus.github.io/iverilog/

**Tools:**
- OSS CAD Suite: https://github.com/YosysHQ/oss-cad-suite-build
- GTKWave: http://gtkwave.sourceforge.net/
- OpenLane: https://openlane.readthedocs.io/

**Community:**
- Discord: https://tinytapeout.com/discord
- GitHub Discussions: Open issues/discussions in repo

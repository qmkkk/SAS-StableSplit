# SAS: Stable-Assignment Splitting for Sparse Triangular Accelerators

This repository contains the **code** of the SAS (StableSplit) compiler
transformation for shared-memory sparse triangular solve (SpTRSV)
accelerators: core transformation and allocation modules, RTL repair patches,
physical-implementation and power-estimation flows, independent checkers,
test benches, and C++ interposition hooks.

> **Artifact policy.** This repository intentionally contains **no
> experimental data, no measured results, and no manuscript**. The method
> code is shared for reproducibility of the *procedure*; the numerical
> outcomes, recorded transactions, and the paper are released separately
> through the authors. This is a deliberate pre-submission arrangement.

## What is here

| Path | Contents |
|---|---|
| `src/` | Core SAS transformation and allocation modules (Python, NumPy/SciPy). |
| `verify/` | Independent checkers: equivalence proofs for the repaired PE and crossbar, power/activity analysis, replay and numerical verification. |
| `rtl_patches/` | Unified diffs of the physical repairs applied to the reference RTL (acyclic PE, one-hot crossbar, reset and memory-inference fixes). The patches contain only the changes; the reference RTL is third-party and is not redistributed. |
| `tb/` | SystemVerilog test benches written for this work (drive the reference RTL; the reference RTL itself is third-party). |
| `flows/` | Vivado Tcl flows: synthesis, implementation, hold repair, conditional interface timing, and post-route power estimation. |
| `wrapper/` | C++ interposition hooks and measurement programs used with the third-party backend library (not included here). |

## Dependencies and third-party boundaries

The following are **not** redistributed in this repository; obtain them from
their respective owners as described.

1. **Reference SpTRSV accelerator RTL and backend library.** The original
   medium-granularity dataflow accelerator, its RTL, and its `stpucpl` backend
   are the work of Qian Chen, Xiaofeng Yang, and Shengli Lu (IEEE TVLSI,
   *Efficient Hardware Accelerator Based on Medium Granularity Dataflow for
   SpTRSV*). The repairs in `rtl_patches/` are diffs *against* that reference;
   the reference files must be obtained from its authors.
2. **`cktso` solver library.** The commercial solver library used by the
   factorization stage is licensed software with a key file and is not
   distributed here.
3. **AMD/Xilinx floating-point IP.** The zero-latency FP32 add/multiply IP
   cores used in the physical derivative are generated inside Vivado and are
   subject to AMD licensing terms.

## Running the method

The core transformation and allocation modules are pure Python (NumPy,
SciPy). They operate on a SuiteSparse lower-triangular factor and produce the
SAS expanded graph and assignment. RTL simulation additionally requires the
third-party reference RTL; apply `rtl_patches/`, add `tb/`, and drive the
`flows/` Tcl scripts. The checker scripts under `verify/` are self-contained
code and read whatever data directories the user supplies.

## License and attribution

Original code in this repository is released under the MIT License (see
`LICENSE`). Third-party components and their provenance are listed in
`THIRD_PARTY_NOTICES.md`; none are bundled.

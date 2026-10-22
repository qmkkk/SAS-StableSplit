# Third-party notices and provenance

This repository intentionally does **not** bundle third-party code. The
following components are referenced by the method, RTL patches, flows, or
scripts, and must be obtained from their respective owners. Redistribution
here is avoided to respect their licenses and provenance.

## 1. Reference SpTRSV accelerator (RTL and backend library)

- **Origin:** Qian Chen, Xiaofeng Yang, and Shengli Lu, "Efficient Hardware
  Accelerator Based on Medium Granularity Dataflow for SpTRSV," IEEE
  Transactions on Very Large Scale Integration (VLSI) Systems.
- **What is referenced:** the original medium-granularity dataflow accelerator
  RTL and its `stpucpl` compiler/backend library.
- **Relation to this repository:** `rtl_patches/` contains unified diffs of
  the physical repairs applied *on top of* that reference. The patches do not
  include the reference files. `tb/` test benches and the `wrapper/` C++
  interposition hooks drive and link against that library, which must be
  obtained from its authors.
- **Not bundled:** reference RTL, `stpucpl.h`, `libstpucpl.a`.

## 2. CKTSO solver library

- **Origin:** commercial sparse-direct solver library, distributed with a
  license-key file.
- **What it is used for:** factorization stage of the experiment pipeline.
- **Not bundled:** `cktso.h`, `libcktso.so`, key files. License terms apply.

## 3. AMD/Xilinx floating-point IP

- **Origin:** AMD Vivado IP catalog.
- **What it is used for:** zero-latency FP32 add and multiply cores in the
  physical derivative and in exact AMD-IP replay.
- **Not bundled:** generated IP netlists, DCP checkpoints, or simulation
  models. They are generated inside Vivado subject to AMD licensing terms.

## 4. SuiteSparse Matrix Collection

- **Origin:** the lower-triangular factors used by the method are from the
  SuiteSparse (formerly University of Florida) Sparse Matrix Collection.
- **Not bundled:** the matrix files are fetched by the method scripts from
  their public repository as documented in `src/`.

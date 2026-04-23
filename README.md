# HFGA-Hybrid-Formal-Graph-Analysis

This repository is designed to develop the course topic into a bug detection tool that can be used in embedded software design.

## Original Course Topic

Name: Software Bug Detection using Call Graphs and Invariant Inference

Purpose: Develop an automated pipeline to detect logic errors (especially missing function pairs like malloc/free, open/close) by analyzing the program structure graphically.

Main components:

- Call Graph: Represents the relationship between functions (vertices are functions, edges are function calls). The group uses both static analysis (Clang/LLVM) and dynamic analysis (Valgrind).
- Graph Simplification: Uses techniques such as Total Reduction or Zero-One-Many to simplify data, making computation faster.
- Invariant Inference: This is the "heart" of the method. Based on statistical probability:
  - Support: The frequency of function pairs appearing.
  - Confidence: The probability that function B appears if function A appears.
  - Example: If in 100 calls to lock(), 99 are followed by unlock(), the system infers that lock/unlock is an "invariant". The 100th call to lack unlock() will be flagged as an error.

## Gaps and Impracticality of the method

### Logic flaws in probability-based calculation for false positives/negatives

Dependency on `threshold` values for support and confidence can lead to misclassification of function pairs, resulting in false positives (incorrectly flagged as errors) or false negatives (missed actual errors).

In embedded systems, there are certains error handlers or interrupts is only called in specific conditions, which may not be captured in the training data, leading to low support and confidence for valid function pairs.

### Lacks of context-awareness

The original report used Total Reduction method to simplify the call graph, which may lead to loss of important contextual information. For example, in embedded systems, certain function pairs may only be valid in specific contexts (e.g., within an interrupt handler or under certain conditions). The lack of context-awareness can lead to incorrect inferences about function pairs.

For instance, `read()` with `close()` may be a valid pair in a file handling context, but using `read()` from static buffer may not require `close()`. The original method may incorrectly flag the latter as an error due to lack of context.

### Specific Weaknesses in Embedded Systems

Memory profiling is limited to only some of peripheral interactions like ITM, SWO, and DWT. Many other interactions with peripherals (e.g., GPIO, UART) are not captured, which can lead to incomplete call graphs and missed bugs. In addition, using Valgrind for dynamic analysis in embedded systems is impractical due to:

- Resource Constraints: Embedded systems often have limited CPU and memory resources, making it difficult to run Valgrind effectively. On the other side, simulating embedded software on a PC may not accurately reflect the behavior of the real hardware, leading to inaccurate call graphs and bug detection results.

- Mismatch between Simulation and Reality: Dynamic analysis may change the actual execution behavior of the embedded software, leading to Heisenbugs (bugs that disappear or change behavior when you try to observe them). This can result in false positives or negatives in bug detection.

- Conventional call graphs do not represent asynchronous interrupt execution flows. In embedded systems, a function may not call another function directly but through a flag variable handled in the ISR (Interrupt Service Routine). Graphs in reports are completely "blind" to this structure.

### Design and Simulation Phases

- The previous method is "run-only" and does not offer much support for the design phase. For high applicability in design, methods such as Model Checking or Formal Verification are needed rather than statistical inference based on execution traces.
- The gap between simulation and reality by using only a sample dataset (30 C++ programs) is too small. In embedded software, interactions with registers and peripherals are the primary source of errors, but call graphs focus only on the relationships between software functions.

## New Philosophy Design

Instead of relying on statistical inference, we will use a more formal method to analyze the call graph and detect potential bugs. This involves:

- KLEE (LLVM) for symbolic execution to explore all possible execution paths and identify potential bugs without relying on execution traces.
- opt (LLVM) to trace and perform call graph design.
- Valgrind on simulation platform to capture memory interactions and peripheral interactions that are not captured in the call graph.

## Roadmap for development process

Stage 1: Multilayer Graph Construction
Stage 2: Path Exploration with KLEE
Stage 3: Temporal Logic Invariants
Stage 4: Dynamic Debugging in a Virtual Environment
Stage 5: Anomoly Detection and Reporting

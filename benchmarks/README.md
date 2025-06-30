# Browser Agent Benchmarks

This directory contains all benchmark-related files for testing browser agent performance.

## Files

- **`benchmark_browser_agents.py`** - Main benchmarking script
- **`run_benchmark_example.py`** - Example usage script
- **`test_browser_agent.py`** - Single agent test script
- **`BENCHMARK_README.md`** - Detailed documentation
- **`benchmark_results_*.json`** - Benchmark result files

## Usage

### From the project root:
```bash
# Run a basic benchmark
python benchmarks/benchmark_browser_agents.py "your task description"

# Run with examples
python benchmarks/benchmark_browser_agents.py "task" examples.json

# Run the example script
python benchmarks/run_benchmark_example.py

# Test a single agent
python benchmarks/test_browser_agent.py recording.json
```

### From the benchmarks directory:
```bash
cd benchmarks

# Run a basic benchmark
python benchmark_browser_agents.py "your task description"

# Run with examples
python benchmark_browser_agents.py "task" ../examples.json

# Run the example script
python run_benchmark_example.py

# Test a single agent
python test_browser_agent.py ../recording.json
```

## Results

Benchmark results are automatically saved to `benchmark_results_YYYYMMDD_HHMMSS.json` files in this directory.

## Configuration

All scripts automatically handle the correct import paths when run from either the project root or the benchmarks directory. 
# Browser Agent Benchmarking System

This system allows you to run comprehensive benchmarks comparing browser agents with and without examples to measure performance improvements.

## 🚀 Quick Start

### 1. Basic Benchmark (Without Examples)
```bash
python benchmark_browser_agents.py "go through ycombinator.com and travel to the startup directory"
```

### 2. Benchmark with Examples
```bash
python benchmark_browser_agents.py "go through ycombinator.com and travel to the startup directory" examples.json
```

### 3. Custom Number of Runs
```bash
python benchmark_browser_agents.py "fill out the contact form" examples.json 10 10
```

## 📊 What Gets Measured

The benchmark tracks:
- **Execution Time**: How long each agent takes to complete the task
- **Success Rate**: Percentage of successful completions
- **Steps Taken**: Estimated number of actions performed
- **Performance Comparison**: Time and efficiency improvements with examples

## 🔧 Configuration

### Headless Mode
All agents run in headless mode by default for:
- Consistent performance across runs
- Faster execution (no GUI overhead)
- Better resource utilization

### Environment Variables
The system automatically configures:
- `BROWSER_USE_HEADLESS=true`
- `PLAYWRIGHT_HEADLESS=true`
- `BROWSER_USE_VIEWPORT_WIDTH=1920`
- `BROWSER_USE_VIEWPORT_HEIGHT=1080`
- `BROWSER_USE_DISABLE_IMAGES=true` (for speed)

## 📈 Output

### Console Output
```
🧪 Browser Agent Benchmark
============================================================
📋 Task: go through ycombinator.com and travel to the startup directory
📚 Examples file: examples.json
👻 Headless mode: True
📚 Runs with examples: 5
🚀 Runs without examples: 5
⏰ Started at: 2024-01-15 14:30:00

📊 BENCHMARK RESULTS
============================================================

📚 WITH EXAMPLES (5 runs):
   Success rate: 100.0% (5/5)
   Average time: 45.23s
   Time range: 42.10s - 48.50s
   Median time: 44.80s
   Average steps: 12.4
   Steps range: 11 - 14

🚀 WITHOUT EXAMPLES (5 runs):
   Success rate: 80.0% (4/5)
   Average time: 67.45s
   Time range: 58.20s - 89.30s
   Median time: 65.10s
   Average steps: 18.2
   Steps range: 15 - 22

⚡ PERFORMANCE COMPARISON:
   Time improvement with examples: 32.9%
   Step efficiency improvement: 31.9%
```

### JSON Results File
Detailed results are saved to `benchmark_results_YYYYMMDD_HHMMSS.json` containing:
- Individual run details
- Statistical analysis
- Performance comparisons
- Error information

## 🎯 Example Tasks

### Good Benchmark Tasks
- **Navigation Tasks**: "Go to X website and navigate to Y section"
- **Form Filling**: "Fill out the contact form on example.com"
- **Search Tasks**: "Search for 'python tutorials' on Google"
- **E-commerce**: "Find and add the first item to cart on amazon.com"

### Task Guidelines
- Be specific about the goal
- Include clear success criteria
- Avoid tasks that require login (unless you have test credentials)
- Keep tasks reasonably complex (5-20 steps)

## 🔄 Running Multiple Benchmarks

### Parallel Execution
The system runs agents in parallel (up to 5 simultaneously) for faster benchmarking.

### Resource Management
- Each agent runs in its own browser instance
- Headless mode reduces memory usage
- Images disabled for faster loading

## 📋 Command Line Options

```bash
python benchmark_browser_agents.py "task" [examples_file] [runs_with_examples] [runs_without_examples]
```

### Parameters:
1. **task** (required): The task description
2. **examples_file** (optional): Path to JSON file with recorded examples
3. **runs_with_examples** (optional): Number of runs with examples (default: 5)
4. **runs_without_examples** (optional): Number of runs without examples (default: 5)

## 🛠️ Troubleshooting

### Common Issues

1. **Import Errors**
   ```
   ❌ Error importing web_browse_executor
   ```
   - Make sure you're running from the project root directory
   - Check that `jarvus_app` is in your Python path

2. **Browser Launch Failures**
   ```
   ❌ Browser agent failed with error: Failed to launch browser
   ```
   - Ensure Playwright is installed: `playwright install`
   - Check system resources (memory, CPU)

3. **Timeout Errors**
   ```
   ❌ Browser agent failed with error: Timeout
   ```
   - Increase timeout in the web.py file
   - Check network connectivity
   - Simplify the task

### Performance Tips

1. **Reduce Number of Runs** for faster testing:
   ```bash
   python benchmark_browser_agents.py "task" examples.json 3 3
   ```

2. **Use Simple Tasks** for initial testing:
   ```bash
   python benchmark_browser_agents.py "go to google.com"
   ```

3. **Monitor System Resources** during benchmarks:
   - CPU usage
   - Memory consumption
   - Network activity

## 📊 Interpreting Results

### Success Rate
- **100%**: Task completed successfully every time
- **80-99%**: Generally reliable, minor variations
- **<80%**: May indicate task complexity or environmental issues

### Time Improvements
- **>50%**: Excellent improvement with examples
- **20-50%**: Good improvement
- **<20%**: Minimal improvement (task may be too simple)

### Step Efficiency
- **>30%**: Examples significantly reduce redundant actions
- **10-30%**: Moderate efficiency gain
- **<10%**: Examples provide minimal guidance

## 🔬 Advanced Usage

### Custom Benchmark Script
```python
from benchmark_browser_agents import BrowserAgentBenchmark

# Create custom benchmark
benchmark = BrowserAgentBenchmark(
    task_description="Your custom task",
    examples_file="your_examples.json",
    num_runs_with_examples=10,
    num_runs_without_examples=10,
    headless=True
)

# Run and get results
results = benchmark.run_benchmark()
print(f"Success rate with examples: {results['statistics']['with_examples']['success_rate']:.1f}%")
```

### Batch Testing
```bash
# Test multiple tasks
for task in "task1" "task2" "task3"; do
    python benchmark_browser_agents.py "$task" examples.json 3 3
done
```

## 📝 Notes

- All agents run in headless mode for consistency
- Results are automatically saved to timestamped JSON files
- The system handles errors gracefully and continues with other runs
- Parallel execution may cause slight variations in timing due to resource contention 
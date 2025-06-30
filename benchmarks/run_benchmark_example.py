#!/usr/bin/env python3
"""
Example script demonstrating how to run browser agent benchmarks.
"""

import sys
import os

# Add parent directory to path since we're now in benchmarks/ subdirectory
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from benchmark_browser_agents import BrowserAgentBenchmark

def main():
    """Example benchmark run."""
    
    # Example task
    task = "go through ycombinator.com and travel to the startup directory. On the startup directory page, filter for startups that are in fintech. Click on the first startup that appears on the list"
    
    # Examples file (optional)
    examples_file = "examples.json"  # Change this to your actual examples file
    
    print("🚀 Starting Browser Agent Benchmark Example")
    print("=" * 50)
    
    # Create benchmark with 3 runs each (for faster testing)
    benchmark = BrowserAgentBenchmark(
        task_description=task,
        examples_file=examples_file,
        num_runs_with_examples=3,
        num_runs_without_examples=3,
        headless=True
    )
    
    try:
        results = benchmark.run_benchmark()
        print("\n🎉 Example benchmark completed!")
        
        # Print a quick summary
        with_examples = results['statistics']['with_examples']
        without_examples = results['statistics']['without_examples']
        
        print(f"\n📊 Quick Summary:")
        print(f"   With examples: {with_examples['success_rate']:.1f}% success, {with_examples['avg_time']:.2f}s avg")
        print(f"   Without examples: {without_examples['success_rate']:.1f}% success, {without_examples['avg_time']:.2f}s avg")
        
    except Exception as e:
        print(f"❌ Example benchmark failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 
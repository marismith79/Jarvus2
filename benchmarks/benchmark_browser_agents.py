#!/usr/bin/env python3
"""
Comprehensive browser agent benchmarking script.
Runs multiple agents in parallel with and without examples to compare performance.
"""

import json
import sys
import os
import asyncio
import time
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any, Optional
import statistics
from dataclasses import dataclass
from pathlib import Path

@dataclass
class AgentResult:
    """Data class to store agent execution results."""
    run_id: str
    has_examples: bool
    success: bool
    execution_time: float
    error: Optional[str] = None
    result: Optional[str] = None
    steps_taken: Optional[int] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None

class BrowserAgentBenchmark:
    """Benchmark class for testing browser agents with and without examples."""
    
    def __init__(self, task_description: str, examples_file: Optional[str] = None, 
                 num_runs_with_examples: int = 5, num_runs_without_examples: int = 5,
                 headless: bool = True):
        self.task_description = task_description
        self.examples_file = examples_file
        self.num_runs_with_examples = num_runs_with_examples
        self.num_runs_without_examples = num_runs_without_examples
        self.headless = headless
        self.results: List[AgentResult] = []
        
        # Load examples if provided
        self.examples_data = None
        if examples_file and os.path.exists(examples_file):
            try:
                with open(examples_file, 'r') as f:
                    self.examples_data = json.load(f)
                print(f"✅ Loaded examples from: {examples_file}")
            except Exception as e:
                print(f"❌ Error loading examples file: {e}")
                self.examples_data = None
        
        # Import the web browse executor
        try:
            # Add parent directory to path since we're now in benchmarks/ subdirectory
            parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            sys.path.append(parent_dir)
            from jarvus_app.services.tools.web import web_browse_executor
            self.web_browse_executor = web_browse_executor
        except ImportError as e:
            print(f"❌ Error importing web_browse_executor: {e}")
            raise
    
    def run_single_agent(self, run_id: str, has_examples: bool) -> AgentResult:
        """Run a single agent instance and return the result."""
        print(f"🚀 Starting agent run {run_id} ({'with' if has_examples else 'without'} examples)")
        
        start_time = time.time()
        
        try:
            # Build parameters
            parameters = {
                "task": self.task_description
            }
            
            if has_examples and self.examples_data:
                parameters["recorded_actions"] = self.examples_data
            
            # Execute the agent
            result = self.web_browse_executor("web", {
                "operation": "web_browse",
                "parameters": parameters
            })
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Extract timing information
            timing = result.get('timing', {})
            start_time_str = timing.get('start_time', 'Unknown')
            end_time_str = timing.get('end_time', 'Unknown')
            
            # Try to extract steps taken from the result
            steps_taken = None
            if result.get('success') and result.get('result'):
                # This is a rough estimate - you might need to parse the result more carefully
                result_text = str(result.get('result', ''))
                # Count common action indicators
                action_indicators = ['click', 'type', 'navigate', 'scroll', 'wait', 'find']
                steps_taken = sum(1 for indicator in action_indicators if indicator in result_text.lower())
            
            return AgentResult(
                run_id=run_id,
                has_examples=has_examples,
                success=result.get('success', False),
                execution_time=execution_time,
                error=result.get('error'),
                result=result.get('result'),
                steps_taken=steps_taken,
                start_time=start_time_str,
                end_time=end_time_str
            )
            
        except Exception as e:
            end_time = time.time()
            execution_time = end_time - start_time
            
            return AgentResult(
                run_id=run_id,
                has_examples=has_examples,
                success=False,
                execution_time=execution_time,
                error=str(e)
            )
    
    def run_benchmark(self) -> Dict[str, Any]:
        """Run the complete benchmark with all agents."""
        print("🧪 Browser Agent Benchmark")
        print("=" * 60)
        print(f"📋 Task: {self.task_description}")
        print(f"📚 Examples file: {self.examples_file or 'None'}")
        print(f"👻 Headless mode: {self.headless}")
        print(f"📚 Runs with examples: {self.num_runs_with_examples}")
        print(f"🚀 Runs without examples: {self.num_runs_without_examples}")
        print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Create all run tasks
        tasks = []
        
        # Add runs with examples
        for i in range(self.num_runs_with_examples):
            run_id = f"with_examples_{i+1}"
            tasks.append((run_id, True))
        
        # Add runs without examples
        for i in range(self.num_runs_without_examples):
            run_id = f"without_examples_{i+1}"
            tasks.append((run_id, False))
        
        # Run all agents in parallel
        print(f"🚀 Starting {len(tasks)} agent runs in parallel...")
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=min(len(tasks), 5)) as executor:
            # Submit all tasks
            future_to_task = {
                executor.submit(self.run_single_agent, run_id, has_examples): (run_id, has_examples)
                for run_id, has_examples in tasks
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_task):
                run_id, has_examples = future_to_task[future]
                try:
                    result = future.result()
                    self.results.append(result)
                    
                    status = "✅ SUCCESS" if result.success else "❌ FAILED"
                    print(f"📊 {run_id}: {status} ({result.execution_time:.2f}s)")
                    
                    if not result.success and result.error:
                        print(f"   Error: {result.error[:100]}...")
                    
                except Exception as e:
                    print(f"❌ {run_id}: Exception occurred: {e}")
        
        total_time = time.time() - start_time
        
        # Generate benchmark report
        return self.generate_report(total_time)
    
    def generate_report(self, total_benchmark_time: float) -> Dict[str, Any]:
        """Generate a comprehensive benchmark report."""
        print("\n" + "=" * 60)
        print("📊 BENCHMARK RESULTS")
        print("=" * 60)
        
        # Separate results by type
        with_examples = [r for r in self.results if r.has_examples]
        without_examples = [r for r in self.results if not r.has_examples]
        
        # Calculate statistics
        def calculate_stats(results: List[AgentResult]) -> Dict[str, Any]:
            if not results:
                return {"count": 0, "success_rate": 0, "avg_time": 0, "min_time": 0, "max_time": 0}
            
            successful = [r for r in results if r.success]
            times = [r.execution_time for r in successful]
            steps = [r.steps_taken for r in successful if r.steps_taken is not None]
            
            return {
                "count": len(results),
                "success_count": len(successful),
                "success_rate": len(successful) / len(results) * 100,
                "avg_time": statistics.mean(times) if times else 0,
                "min_time": min(times) if times else 0,
                "max_time": max(times) if times else 0,
                "median_time": statistics.median(times) if times else 0,
                "avg_steps": statistics.mean(steps) if steps else 0,
                "min_steps": min(steps) if steps else 0,
                "max_steps": max(steps) if steps else 0
            }
        
        with_stats = calculate_stats(with_examples)
        without_stats = calculate_stats(without_examples)
        
        # Print detailed results
        print(f"\n📚 WITH EXAMPLES ({with_stats['count']} runs):")
        print(f"   Success rate: {with_stats['success_rate']:.1f}% ({with_stats['success_count']}/{with_stats['count']})")
        print(f"   Average time: {with_stats['avg_time']:.2f}s")
        print(f"   Time range: {with_stats['min_time']:.2f}s - {with_stats['max_time']:.2f}s")
        print(f"   Median time: {with_stats['median_time']:.2f}s")
        if with_stats['avg_steps'] > 0:
            print(f"   Average steps: {with_stats['avg_steps']:.1f}")
            print(f"   Steps range: {with_stats['min_steps']} - {with_stats['max_steps']}")
        
        print(f"\n🚀 WITHOUT EXAMPLES ({without_stats['count']} runs):")
        print(f"   Success rate: {without_stats['success_rate']:.1f}% ({without_stats['success_count']}/{without_stats['count']})")
        print(f"   Average time: {without_stats['avg_time']:.2f}s")
        print(f"   Time range: {without_stats['min_time']:.2f}s - {without_stats['max_time']:.2f}s")
        print(f"   Median time: {without_stats['median_time']:.2f}s")
        if without_stats['avg_steps'] > 0:
            print(f"   Average steps: {without_stats['avg_steps']:.1f}")
            print(f"   Steps range: {without_stats['min_steps']} - {without_stats['max_steps']}")
        
        # Performance comparison
        if with_stats['avg_time'] > 0 and without_stats['avg_time'] > 0:
            time_improvement = ((without_stats['avg_time'] - with_stats['avg_time']) / without_stats['avg_time']) * 100
            print(f"\n⚡ PERFORMANCE COMPARISON:")
            print(f"   Time improvement with examples: {time_improvement:.1f}%")
            
            if with_stats['avg_steps'] > 0 and without_stats['avg_steps'] > 0:
                step_improvement = ((without_stats['avg_steps'] - with_stats['avg_steps']) / without_stats['avg_steps']) * 100
                print(f"   Step efficiency improvement: {step_improvement:.1f}%")
        
        # Individual run details
        print(f"\n📋 INDIVIDUAL RUN DETAILS:")
        for result in self.results:
            status = "✅" if result.success else "❌"
            examples_indicator = "📚" if result.has_examples else "🚀"
            print(f"   {examples_indicator} {result.run_id}: {status} {result.execution_time:.2f}s", end="")
            if result.steps_taken:
                print(f" ({result.steps_taken} steps)", end="")
            if not result.success and result.error:
                print(f" - {result.error[:50]}...", end="")
            print()
        
        print(f"\n⏱️  Total benchmark time: {total_benchmark_time:.2f}s")
        print(f"📅 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Save detailed results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"benchmark_results_{timestamp}.json"
        
        detailed_results = {
            "benchmark_info": {
                "task": self.task_description,
                "examples_file": self.examples_file,
                "headless": self.headless,
                "runs_with_examples": self.num_runs_with_examples,
                "runs_without_examples": self.num_runs_without_examples,
                "total_benchmark_time": total_benchmark_time,
                "started_at": datetime.now().isoformat()
            },
            "statistics": {
                "with_examples": with_stats,
                "without_examples": without_stats
            },
            "individual_results": [
                {
                    "run_id": r.run_id,
                    "has_examples": r.has_examples,
                    "success": r.success,
                    "execution_time": r.execution_time,
                    "error": r.error,
                    "result": r.result,
                    "steps_taken": r.steps_taken,
                    "start_time": r.start_time,
                    "end_time": r.end_time
                }
                for r in self.results
            ]
        }
        
        with open(results_file, 'w') as f:
            json.dump(detailed_results, f, indent=2)
        
        print(f"💾 Detailed results saved to: {results_file}")
        
        return detailed_results

def main():
    """Main function to run the benchmark."""
    if len(sys.argv) < 2:
        print("Usage: python benchmark_browser_agents.py \"task description\" [examples_file] [runs_with_examples] [runs_without_examples]")
        print("\nExample:")
        print("  python benchmark_browser_agents.py \"go through ycombinator.com and travel to the startup directory\"")
        print("  python benchmark_browser_agents.py \"fill out the contact form\" examples.json 5 5")
        return
    
    task_description = sys.argv[1]
    examples_file = sys.argv[2] if len(sys.argv) > 2 else None
    runs_with_examples = int(sys.argv[3]) if len(sys.argv) > 3 else 5
    runs_without_examples = int(sys.argv[4]) if len(sys.argv) > 4 else 5
    
    # Create and run benchmark
    benchmark = BrowserAgentBenchmark(
        task_description=task_description,
        examples_file=examples_file,
        num_runs_with_examples=runs_with_examples,
        num_runs_without_examples=runs_without_examples,
        headless=True  # Always run in headless mode for benchmarking
    )
    
    try:
        results = benchmark.run_benchmark()
        print("\n🎉 Benchmark completed successfully!")
    except Exception as e:
        print(f"❌ Benchmark failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 
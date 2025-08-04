import os
import json
import datetime
from typing import Dict, Any, List

RESULTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'test_results')
RESULTS_FILE = os.path.join(RESULTS_DIR, 'last_run_results.json')
HTML_FILE = os.path.join(RESULTS_DIR, 'last_run_results.html')

os.makedirs(RESULTS_DIR, exist_ok=True)

def log_test_result(test_name: str, status: str, response: Any = None, error: str = None, extra: Dict[str, Any] = None):
    """Append a test result to the results file."""
    result = {
        'test_name': test_name,
        'status': status,
        'timestamp': datetime.datetime.utcnow().isoformat(),
        'response': response,
        'error': error,
    }
    if extra:
        result.update(extra)
    
    # Read existing results
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, 'r') as f:
            results = json.load(f)
    else:
        results = []
    results.append(result)
    with open(RESULTS_FILE, 'w') as f:
        json.dump(results, f, indent=2)

def log_test_result_to_stdout(test_name: str, status: str, response: Any = None, error: str = None, extra: Dict[str, Any] = None):
    """Append a test result as a JSON string (one per line) to test_results/test_run_log.txt, handling non-serializable objects."""
    def default_serializer(obj):
        if hasattr(obj, 'to_dict'):
            return obj.to_dict()
        return str(obj)
    result = {
        'test_name': test_name,
        'status': status,
        'timestamp': datetime.datetime.utcnow().isoformat(),
        'response': response,
        'error': error,
    }
    if extra:
        result.update(extra)
    log_file = os.path.join(RESULTS_DIR, 'test_run_log.txt')
    with open(log_file, 'a') as f:
        f.write(json.dumps(result, default=default_serializer) + '\n')
    
def reset_results():
    """Clear the results file before a new test run."""
    with open(RESULTS_FILE, 'w') as f:
        json.dump([], f)


def get_test_results() -> Dict[str, Any]:
    """Get all test results from the results file."""
    if not os.path.exists(RESULTS_FILE):
        return {}
    
    with open(RESULTS_FILE, 'r') as f:
        results = json.load(f)
    
    # Convert to dictionary format for easier access
    test_results = {}
    for result in results:
        test_results[result['test_name']] = {
            'status': result['status'],
            'timestamp': result['timestamp'],
            'error': result.get('error'),
            'response': result.get('response')
        }
    
    return test_results


def generate_html_report(report_data: Dict[str, Any] = None, output_file: str = None):
    """Generate an HTML report from test results."""
    if report_data is None:
        # Use the default results file
        if not os.path.exists(RESULTS_FILE):
            return
        with open(RESULTS_FILE, 'r') as f:
            results = json.load(f)
    else:
        # Use provided report data
        results = report_data.get('detailed_test_results', {})
        if isinstance(results, dict):
            # Convert dict format to list format
            results_list = []
            for test_name, result in results.items():
                results_list.append({
                    'test_name': test_name,
                    'status': result['status'],
                    'timestamp': result.get('timestamp', ''),
                    'error': result.get('error', ''),
                    'response': result.get('response', '')
                })
            results = results_list
    
    if output_file is None:
        output_file = HTML_FILE
    
    html = [
        '<html><head><title>Memory System Test Results</title>',
        '<style>',
        'body{font-family:sans-serif; margin:20px;}',
        '.pass{color:green; font-weight:bold;}',
        '.fail{color:red; font-weight:bold;}',
        'table{border-collapse:collapse; width:100%; margin-top:20px;}',
        'td,th{border:1px solid #ccc; padding:8px; text-align:left;}',
        'th{background-color:#f2f2f2;}',
        '.summary{background-color:#f8f9fa; padding:15px; border-radius:5px; margin-bottom:20px;}',
        '.error{background-color:#fff3cd; border:1px solid #ffeaa7; padding:10px; border-radius:3px;}',
        'pre{background-color:#f8f9fa; padding:10px; border-radius:3px; overflow-x:auto;}',
        '</style></head><body>',
        '<h1>Memory System Test Results</h1>'
    ]
    
    # Add summary if available
    if report_data and 'summary' in report_data:
        summary = report_data['summary']
        html.extend([
            '<div class="summary">',
            f'<h2>Test Summary</h2>',
            f'<p><strong>Total Test Files:</strong> {summary["total_test_files"]}</p>',
            f'<p><strong>Passed:</strong> {summary["passed_test_files"]} ✅</p>',
            f'<p><strong>Failed:</strong> {summary["failed_test_files"]} ❌</p>',
            f'<p><strong>Success Rate:</strong> {summary["success_rate"]:.1f}%</p>',
            f'<p><strong>Total Time:</strong> {summary["total_time_seconds"]:.2f} seconds</p>',
            '</div>'
        ])
    
    html.extend([
        f'<p><strong>Total tests:</strong> {len(results)}</p>',
        '<table><tr><th>Test Name</th><th>Status</th><th>Timestamp</th><th>Error</th><th>Response</th></tr>'
    ])
    
    for r in results:
        error_cell = f'<div class="error">{r.get("error", "")}</div>' if r.get('error') else ''
        response_cell = f'<pre>{json.dumps(r.get("response", ""), indent=2) if r.get("response") else ""}</pre>'
        
        html.append(
            f"<tr><td>{r['test_name']}</td>"
            f"<td class='{r['status']}'>{r['status']}</td>"
            f"<td>{r.get('timestamp', '')}</td>"
            f"<td>{error_cell}</td>"
            f"<td>{response_cell}</td></tr>"
        )
    
    html.append('</table></body></html>')
    
    with open(output_file, 'w') as f:
        f.write('\n'.join(html))


def get_summary() -> Dict[str, Any]:
    """Return a summary of the last run results."""
    if not os.path.exists(RESULTS_FILE):
        return {}
    with open(RESULTS_FILE, 'r') as f:
        results = json.load(f)
    total = len(results)
    passed = sum(1 for r in results if r['status'] == 'pass')
    failed = sum(1 for r in results if r['status'] == 'fail')
    return {'total': total, 'passed': passed, 'failed': failed, 'results': results} 
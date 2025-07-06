# Memory System Test Suite

This directory contains a comprehensive test suite for the Jarvus Memory System, covering all aspects from basic CRUD operations to advanced features like hierarchical memory, vector search, and security.

## Test Structure

### Core Tests
- **`test_memory_api.py`** - Basic CRUD operations, retrieval, and search functionality
- **`test_vector_memory.py`** - Vector database integration, semantic search, and content management
- **`test_hierarchical_memory.py`** - Hierarchical memory structure, influence propagation, and context aggregation

### Advanced Features
- **`test_memory_editing_comprehensive.py`** - Memory editing, merging, improvement, and quality assessment
- **`test_bulk_operations.py`** - Bulk create, update, delete, export, import, and analysis operations
- **`test_quality_conflicts.py`** - Quality metrics, conflict detection, and resolution strategies

### System Features
- **`test_prompt_engineering.py`** - Prompt templates, context injection, and optimization
- **`test_monitoring_analytics.py`** - Performance metrics, usage stats, and health monitoring
- **`test_security_privacy.py`** - Encryption, anonymization, access control, and compliance
- **`test_integration_workflows.py`** - Memory synthesis, reasoning chains, and workflow execution

### Test Infrastructure
- **`test_result_logger.py`** - Test result logging and reporting utilities
- **`run_all_tests.py`** - Comprehensive test runner with detailed reporting
- **`conftest.py`** - Pytest configuration and fixtures
- **`pytest.ini`** - Pytest configuration settings

## Running Tests

### Run All Tests
```bash
# From the project root
python tests/run_all_tests.py

# Or using pytest directly
pytest tests/ -v
```

### Run Specific Test Categories
```bash
# Core memory functionality
pytest tests/test_memory_api.py -v

# Vector database features
pytest tests/test_vector_memory.py -v

# Hierarchical memory
pytest tests/test_hierarchical_memory.py -v

# Memory editing features
pytest tests/test_memory_editing_comprehensive.py -v

# Security and privacy
pytest tests/test_security_privacy.py -v

# Monitoring and analytics
pytest tests/test_monitoring_analytics.py -v
```

### Run Tests by Markers
```bash
# Run only unit tests
pytest tests/ -m unit -v

# Run only integration tests
pytest tests/ -m integration -v

# Run memory system tests
pytest tests/ -m memory -v

# Run vector database tests
pytest tests/ -m vector -v

# Skip slow tests
pytest tests/ -m "not slow" -v
```

## Test Results

### Generated Reports
- **JSON Report**: `test_results/comprehensive_test_report.json`
- **HTML Report**: `test_results/comprehensive_test_report.html`
- **Individual Test Logs**: `test_results/test_logs.json`

### Report Contents
- Test file execution results
- Individual test pass/fail status
- Performance metrics
- Error details and stack traces
- Summary statistics

## Test Coverage

### Memory System Core (Phase 1)
- ✅ Basic CRUD operations
- ✅ Memory retrieval and search
- ✅ Namespace management
- ✅ Tagging system
- ✅ Metadata handling

### Vector Database Integration (Phase 2)
- ✅ Vector storage and retrieval
- ✅ Semantic search
- ✅ Content clustering
- ✅ Hybrid search (SQL + Vector)
- ✅ Performance optimization

### Memory Editing & Improvement (Phase 2)
- ✅ Memory merging
- ✅ Quality assessment
- ✅ Conflict detection
- ✅ Bulk operations
- ✅ Auto-consolidation

### Hierarchical Memory (Phase 3)
- ✅ Hierarchy creation and management
- ✅ Influence propagation
- ✅ Context inheritance
- ✅ Decision context aggregation
- ✅ Hierarchy statistics

### Advanced Features (Phase 4)
- ✅ Prompt engineering
- ✅ Memory synthesis
- ✅ Reasoning chains
- ✅ Personality adaptation
- ✅ Collaborative memory

### Security & Privacy (All Phases)
- ✅ Encryption status
- ✅ Anonymization
- ✅ Access control
- ✅ Audit logging
- ✅ Privacy compliance

### Monitoring & Analytics (All Phases)
- ✅ Performance metrics
- ✅ Usage statistics
- ✅ Health monitoring
- ✅ Alerting system
- ✅ Capacity planning

## Test Data

### Sample Memory Data
The tests use realistic sample data including:
- Vacation planning memories
- Work-related episodes
- Personal preferences
- Procedural knowledge
- Semantic concepts

### Test Scenarios
- User interaction patterns
- Memory evolution over time
- Cross-domain relationships
- Quality degradation scenarios
- Conflict resolution cases

## Configuration

### Environment Setup
Tests automatically configure:
- Test database
- Vector database collections
- Mock services
- Test user accounts
- Sample data

### Test Isolation
Each test runs in isolation with:
- Clean database state
- Independent vector collections
- Mocked external services
- Temporary test data

## Troubleshooting

### Common Issues
1. **Database Connection**: Ensure test database is accessible
2. **Vector DB**: Check ChromaDB installation and configuration
3. **Dependencies**: Install all required packages from `requirements.txt`
4. **Permissions**: Ensure write access to `test_results/` directory

### Debug Mode
```bash
# Run with detailed output
pytest tests/ -v -s --tb=long

# Run single test with debug
pytest tests/test_memory_api.py::test_create_memory -v -s
```

### Test Maintenance
- Update test data when API changes
- Add new tests for new features
- Review and update test coverage
- Maintain test documentation

## Contributing

When adding new tests:
1. Follow the existing naming convention
2. Use the test result logger
3. Add appropriate markers
4. Include realistic test data
5. Update this README if needed

## Performance

### Test Execution Time
- **Unit Tests**: < 1 second each
- **Integration Tests**: 1-5 seconds each
- **Full Suite**: 2-5 minutes total

### Resource Usage
- **Memory**: < 100MB for full suite
- **Database**: Temporary test database
- **Vector DB**: Temporary collections

### Optimization
- Use test fixtures for expensive setup
- Mock external services
- Clean up resources after tests
- Use appropriate test scopes 
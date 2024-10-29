#!/bin/bash

# Navigate to the backend directory
cd "$(dirname "$0")"

# Run non-LLM tests but include async tests
pytest tests/ -v

# Or to run specific test files with LLM tests:
# pytest tests/test_chat_agent.py -v

# Print a message indicating the tests have finished
echo "All tests have been executed."

# TODO: Optionally run LLM tests if environment is configured
if [ "$RUN_LLM_TESTS" = "true" ]; then
    pytest tests/ -v -m "llm"
    echo "LLM tests have been executed."
fi

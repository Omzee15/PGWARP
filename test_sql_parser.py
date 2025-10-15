"""
Test script to verify SQL output parser correctly removes leading comments
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from ai.assistant import SQLOutputParser

# Test cases
test_cases = [
    {
        'name': 'Query with leading comment',
        'input': '''-- Get all active users
SELECT * FROM users WHERE active = true;''',
        'expected_starts_with': 'SELECT'
    },
    {
        'name': 'Query with multiple leading comments',
        'input': '''-- This is a query
-- To get users
-- From the database
SELECT * FROM users;''',
        'expected_starts_with': 'SELECT'
    },
    {
        'name': 'Query with block comment',
        'input': '''/* Get all users */
SELECT * FROM users;''',
        'expected_starts_with': 'SELECT'
    },
    {
        'name': 'Clean query without comments',
        'input': 'SELECT * FROM users;',
        'expected_starts_with': 'SELECT'
    },
    {
        'name': 'Query with inline comments (should keep)',
        'input': '''SELECT * FROM users -- all users
WHERE active = true;''',
        'expected_starts_with': 'SELECT'
    },
    {
        'name': 'Query in code block',
        'input': '''```sql
-- Get users
SELECT * FROM users;
```''',
        'expected_starts_with': 'SELECT'
    }
]

# Run tests
parser = SQLOutputParser()

print("🧪 Testing SQL Output Parser\n")
print("=" * 60)

all_passed = True
for i, test in enumerate(test_cases, 1):
    result = parser.parse(test['input'])
    passed = result.startswith(test['expected_starts_with'])
    
    status = "✅ PASS" if passed else "❌ FAIL"
    all_passed = all_passed and passed
    
    print(f"\nTest {i}: {test['name']}")
    print(f"Status: {status}")
    print(f"Input:\n{test['input'][:100]}...")
    print(f"Output:\n{result[:100]}...")
    print(f"Starts with '{test['expected_starts_with']}': {passed}")
    print("-" * 60)

print("\n" + "=" * 60)
if all_passed:
    print("✅ All tests PASSED!")
else:
    print("❌ Some tests FAILED!")
print("=" * 60)

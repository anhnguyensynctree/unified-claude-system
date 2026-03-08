Analyze test coverage for the current project.

Run the coverage report: [detect from package.json — jest/vitest/pytest/etc]

Report:
  - Overall coverage percentage
  - Files below 80% threshold (list them)
  - Uncovered functions and branches in critical files
  - Recommendation: which gaps are highest priority to fill

Then write tests to bring the most critical gaps above 80%.
Focus on: auth logic, data processing, API handlers first.

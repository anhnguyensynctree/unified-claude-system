Write E2E tests for: $ARGUMENTS

Use Playwright. Focus on critical user flows only.

For each test:
  - Arrange: set up required state
  - Act: perform user actions (clicks, inputs, navigation)
  - Assert: verify user-visible outcomes

Rules:
  - Use data-testid attributes for selectors, not CSS classes
  - No timing assumptions — use waitFor and expect patterns
  - No implementation details — test what users see
  - Tests must be deterministic — no flakiness

Critical flows to cover:
  - Authentication (login, logout, protected routes)
  - Core feature usage (main value of the app)
  - Error states (what users see when things fail)

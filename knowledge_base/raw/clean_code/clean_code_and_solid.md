# Clean Code and SOLID Review Notes

Clean functions should be small, cohesive, and named for one responsibility. Long functions that mix validation, data access, file access, formatting, and side effects are difficult to test and maintain.

The Single Responsibility Principle says a module or class should have one reason to change. Reviewers should flag functions that combine user input parsing, persistence, security decisions, and presentation formatting.

Duplication increases maintenance risk because fixes must be applied consistently in multiple places. Extract repeated logic into named helpers only when the abstraction describes a real concept.

Exception handling should catch specific exception types. Bare exception handlers can hide programming errors, cancellation signals, and security-relevant failures.

Mutable default arguments in Python functions are shared across calls and can leak state between requests.


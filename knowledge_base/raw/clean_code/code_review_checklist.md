# Code Review Checklist

Check security-sensitive sinks: SQL execution, command execution, file access, deserialization, authentication, authorization, and secret handling.

Check maintainability: function length, duplication, unclear names, mixed responsibilities, poor exception handling, mutable defaults, and missing tests.

Check performance: repeated string concatenation in loops, unnecessary nested loops, repeated I/O, and inefficient data structure choices.

Check architecture: dependency direction, separation of concerns, SOLID violations, and whether business rules are isolated from framework code.


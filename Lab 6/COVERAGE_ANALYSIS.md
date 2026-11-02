# Lab 6 Coverage Analysis

The application was exercised through the separate line-coverage and branch-coverage pytest suites. Because the local runtime did not have network access to install third-party packages, `run_lab6_coverage.py` provides a local dynamic verifier for the same test cases. It traces application statements and records both outcomes for every decision and loop.

Results:

- Line suite: 31/31 application statements, 100.0%; 38/38 measured branch outcomes, 100.0%.
- Branch suite: 31/31 application statements, 100.0%; 38/38 measured branch outcomes, 100.0%.

The evidence files contain the terminal output from the verifier command.


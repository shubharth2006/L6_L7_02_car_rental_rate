# Lab 6 Coverage Analysis

The application was exercised through separate pytest suites for line coverage and branch coverage. The reports below were produced with the standard `coverage` commands required by the lab.

Results:

- Line coverage suite: 3 tests passed; `car_rental_rate.py` reached 51/51 statements (100%).
- Branch coverage suite: 14 tests passed; `car_rental_rate.py` reached 51/51 statements and 36/36 branch outcomes (100%).

The terminal-result screenshots (`line_coverage_terminal.png` and `branch_coverage_terminal.png`) and captured command output are in `evidence/`.

## Commands

```text
python -m coverage run -m pytest CodeCoverageTest_car_rental_rate_application.py
python -m coverage report -m

python -m coverage erase
python -m coverage run --branch -m pytest BranchCoverageTest_car_rental_rate_application.py
python -m coverage report -m
```


import ast
import contextlib
import importlib.util
import io
import sys
import types
from pathlib import Path

ROOT = Path(__file__).parent / "Lab 6"
SOURCE = ROOT / "car_rental_rate.py"


class Raises:
    def __init__(self, expected):
        self.expected = expected

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return exc_type is not None and issubclass(exc_type, self.expected)


class Mark:
    def parametrize(self, *args, **kwargs):
        return lambda function: function


def install_pytest_stub():
    pytest = types.ModuleType("pytest")
    pytest.raises = lambda expected: Raises(expected)
    pytest.mark = Mark()
    sys.modules["pytest"] = pytest


class DecisionTransformer(ast.NodeTransformer):
    def __init__(self):
        self.next_id = 1
        self.branch_ids = []

    def wrap(self, node, kind):
        branch_id = self.next_id
        self.next_id += 1
        self.branch_ids.append((branch_id, kind, node.lineno))
        function_name = "__loop__" if kind == "loop" else "__decision__"
        return ast.copy_location(
            ast.Call(
                func=ast.Name(id=function_name, ctx=ast.Load()),
                args=[ast.Constant(branch_id), node],
                keywords=[],
            ),
            node,
        )

    def visit_If(self, node):
        node = self.generic_visit(node)
        node.test = self.wrap(node.test, "if")
        return node

    def visit_IfExp(self, node):
        node = self.generic_visit(node)
        node.test = self.wrap(node.test, "conditional")
        return node

    def visit_For(self, node):
        node = self.generic_visit(node)
        node.iter = self.wrap(node.iter, "loop")
        return node


def load_instrumented_app(decisions):
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"), filename=str(SOURCE))
    transformer = DecisionTransformer()
    tree = transformer.visit(tree)
    ast.fix_missing_locations(tree)

    module = types.ModuleType("car_rental_rate")

    def decision(branch_id, value):
        result = bool(value)
        decisions.setdefault(branch_id, set()).add(result)
        return value

    def loop(branch_id, value):
        result = bool(value)
        outcomes = decisions.setdefault(branch_id, set())
        outcomes.add(result)
        if result:
            outcomes.add(False)
        return value

    module.__dict__["__decision__"] = decision
    module.__dict__["__loop__"] = loop
    sys.modules["car_rental_rate"] = module
    code = compile(tree, str(SOURCE), "exec")
    exec(code, module.__dict__)
    return transformer.branch_ids


def load_tests(filename):
    spec = importlib.util.spec_from_file_location(filename[:-3], ROOT / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_suite(kind):
    install_pytest_stub()
    decisions = {}
    branch_definitions = load_instrumented_app(decisions)
    executed_lines = set()

    def tracer(frame, event, arg):
        if event == "line" and Path(frame.f_code.co_filename).resolve() == SOURCE.resolve():
            executed_lines.add(frame.f_lineno)
        return tracer

    line_test = load_tests("CodeCoverageTest_car_rental_rate_application.py")
    branch_test = load_tests("BranchCoverageTest_car_rental_rate_application.py")
    sys.settrace(tracer)
    try:
        line_test.test_process_rental_fleet_executes_all_application_lines()
        line_test.test_process_rental_fleet_validates_arguments_and_terminal_statuses()
        line_test.test_telematics_covers_no_data_safe_and_ground_paths()
        if kind == "branch":
            branch_test.test_telematics_all_decision_branches()
            status_rows = [
                ("bad", 0, ValueError),
                ([], -1, ValueError),
                ([], 0, {"total_revenue": 0.0, "status": "EMPTY_BATCH"}),
                ([{"is_confirmed": False}], 0, {"total_revenue": 0.0, "status": "EMPTY_BATCH"}),
                ([{"is_confirmed": True, "days": 0}], 0, {"total_revenue": 0.0, "status": "EMPTY_BATCH"}),
                ([{"is_confirmed": True, "days": 0} for _ in range(5)], 0,
                 {"total_revenue": 0.0, "status": "HIGH_RISK_AUDIT"}),
            ]
            for row in status_rows:
                branch_test.test_input_and_final_status_branches(*row)
            pricing_rows = [
                ("luxury", 30, 2, [], 250.0),
                ("suv", 30, 2, [300], 210.0),
                ("economy", 30, 2, [301], 210.4),
                ("other", 24, 1, [0], 70.0),
                ("luxury", 24, 2, [0], 350.0),
                ("economy", 20, 1, [350], 320.0),
                ("suv", 30, 1, [-1, 1], 80.2),
            ]
            for row in pricing_rows:
                branch_test.test_rental_pricing_and_trip_branches(*row)
    finally:
        sys.settrace(None)

    statements = {
        node.lineno
        for node in ast.walk(ast.parse(SOURCE.read_text(encoding="utf-8")))
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.Expr, ast.Return, ast.Raise, ast.Continue, ast.Break))
    }
    covered = statements & executed_lines
    line_percent = 100.0 * len(covered) / len(statements)
    branch_outcomes = sum(len(decisions.get(branch_id, set())) for branch_id, _, _ in branch_definitions)
    branch_total = 2 * len(branch_definitions)
    branch_percent = 100.0 * branch_outcomes / branch_total
    missing = [
        (branch_id, kind, line, sorted(decisions.get(branch_id, set())))
        for branch_id, kind, line in branch_definitions
        if len(decisions.get(branch_id, set())) < 2
    ]
    return line_percent, len(covered), len(statements), branch_percent, branch_outcomes, branch_total, missing


def main():
    for kind in ("line", "branch"):
        result = run_suite(kind)
        print(f"{kind.title()} coverage suite: PASS")
        print(f"Application statements: {result[1]}/{result[2]} covered ({result[0]:.1f}%)")
        print(f"Application branch outcomes: {result[4]}/{result[5]} covered ({result[3]:.1f}%)")
        if result[6]:
            print(f"Uncovered decision outcomes: {result[6]}")


if __name__ == "__main__":
    main()


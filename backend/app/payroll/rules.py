"""
Safe salary rule evaluator — NO eval() used.
Supports FIXED, PERCENTAGE, and FORMULA calculation types.

Formula variables are resolved from the context's computed_values dict.
Only arithmetic operations on known variables are supported.
"""
from typing import Dict, Optional, Any
import re

from app.payroll.context import PayrollContext


# Variables available in formula context
FORMULA_VARS = {
    "CONTRACT_WAGE", "WORKED_DAYS", "TOTAL_WORKING_DAYS", "OVERTIME_HOURS",
    "PAID_LEAVE_DAYS", "UNPAID_LEAVE_DAYS",
    # Rule codes (resolved dynamically)
    "BASIC", "HRA", "TRANSPORT", "GROSS", "PF_EMP", "PT", "NET",
    "OVERTIME", "PF_EMP_CONTRIB", "TDS",
    "BASIC_CONTRACT", "CONTRACT_GROSS", "CONTRACT_NET",
    "STIPEND", "INTERN_NET",
}


def resolve_formula(formula: str, ctx: PayrollContext) -> float:
    """
    Safely evaluate a salary formula string.
    Resolves variables from ctx.computed_values and base context values.
    Supports: +, -, *, /, (, ), and numeric literals.

    This is NOT eval() — it tokenizes and evaluates manually.
    """
    # Build variable namespace
    ns = {
        "CONTRACT_WAGE": ctx.contract_wage,
        "WORKED_DAYS": ctx.worked_days,
        "TOTAL_WORKING_DAYS": float(ctx.total_working_days),
        "OVERTIME_HOURS": ctx.overtime_hours,
        "PAID_LEAVE_DAYS": ctx.paid_leave_days,
        "UNPAID_LEAVE_DAYS": ctx.unpaid_leave_days,
    }
    # Add all computed rule values
    ns.update(ctx.computed_values)

    # Replace variable names in formula with their values
    resolved = formula
    # Sort by length descending to avoid partial replacements
    for var_name in sorted(ns.keys(), key=len, reverse=True):
        resolved = resolved.replace(var_name, str(ns.get(var_name, 0.0)))

    # Now safely evaluate only arithmetic expression
    return _safe_arithmetic(resolved)


def _safe_arithmetic(expr: str) -> float:
    """Evaluate arithmetic expression safely without eval()."""
    expr = expr.strip()

    # Remove spaces
    expr = expr.replace(" ", "")

    # Validate: only digits, operators, dots, parentheses allowed
    if not re.match(r'^[\d\+\-\*\/\.\(\)]+$', expr):
        raise ValueError(f"Unsafe expression detected: {expr}")

    # Use a recursive descent parser
    tokens = _tokenize(expr)
    result, _ = _parse_expr(tokens, 0)
    return result


def _tokenize(expr: str):
    tokens = []
    i = 0
    while i < len(expr):
        if expr[i].isdigit() or expr[i] == '.':
            j = i
            while j < len(expr) and (expr[j].isdigit() or expr[j] == '.'):
                j += 1
            tokens.append(('NUM', float(expr[i:j])))
            i = j
        elif expr[i] in '+-*/()':
            tokens.append(('OP', expr[i]))
            i += 1
        else:
            i += 1
    tokens.append(('END', None))
    return tokens


def _parse_expr(tokens, pos):
    left, pos = _parse_term(tokens, pos)
    while pos < len(tokens) and tokens[pos] == ('OP', '+') or (pos < len(tokens) and tokens[pos] == ('OP', '-')):
        op = tokens[pos][1]
        pos += 1
        right, pos = _parse_term(tokens, pos)
        left = left + right if op == '+' else left - right
    return left, pos


def _parse_term(tokens, pos):
    left, pos = _parse_factor(tokens, pos)
    while pos < len(tokens) and (tokens[pos] == ('OP', '*') or tokens[pos] == ('OP', '/')):
        op = tokens[pos][1]
        pos += 1
        right, pos = _parse_factor(tokens, pos)
        if op == '*':
            left = left * right
        else:
            left = left / right if right != 0 else 0.0
    return left, pos


def _parse_factor(tokens, pos):
    if tokens[pos] == ('OP', '('):
        pos += 1  # consume '('
        val, pos = _parse_expr(tokens, pos)
        if tokens[pos] == ('OP', ')'):
            pos += 1  # consume ')'
        return val, pos
    elif tokens[pos] == ('OP', '-'):
        pos += 1
        val, pos = _parse_factor(tokens, pos)
        return -val, pos
    elif tokens[pos][0] == 'NUM':
        return tokens[pos][1], pos + 1
    return 0.0, pos


def calculate_rule(rule_version: Dict[str, Any], ctx: PayrollContext) -> float:
    """
    Calculate a single salary rule based on its version config.
    Returns the computed amount (positive for earnings, negative not applied here).
    """
    calc_type = rule_version.get("calculation_type", "FIXED")
    category = rule_version.get("category", "")

    if calc_type == "FIXED":
        return float(rule_version.get("fixed_amount") or 0.0)

    elif calc_type == "PERCENTAGE":
        base_code = rule_version.get("base_code", "")
        percentage = float(rule_version.get("percentage") or 0.0)
        base_val = ctx.computed_values.get(base_code, 0.0)
        return base_val * (percentage / 100.0)

    elif calc_type == "FORMULA":
        formula = rule_version.get("formula", "0")
        return resolve_formula(formula, ctx)

    return 0.0

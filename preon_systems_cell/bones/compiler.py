from __future__ import annotations

import ast
import importlib
import math
import operator as op
from typing import Any, Callable

from preon_systems_cell.bones.models import CompiledEnzyme, EnzymeGene

_MATH_NS: dict[str, Any] = {name: getattr(math, name) for name in dir(math) if not name.startswith("_")}

_BINOPS: dict[type, Any] = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.FloorDiv: op.floordiv,
    ast.Mod: op.mod,
    ast.Pow: op.pow,
}
_UNOPS: dict[type, Any] = {
    ast.USub: op.neg,
    ast.UAdd: op.pos,
}


def _safe_eval(node: ast.AST, namespace: dict[str, Any]) -> float:
    """Recursively evaluate an AST node. Only whitelisted constructs are allowed."""
    if isinstance(node, ast.Constant):
        if not isinstance(node.value, (int, float)):
            raise ValueError(f"unsupported constant type: {type(node.value).__name__}")
        return float(node.value)

    if isinstance(node, ast.Name):
        name = node.id
        if name in namespace:
            return float(namespace[name])
        if name in _MATH_NS and not callable(_MATH_NS[name]):
            return float(_MATH_NS[name])  # math constants: pi, e, tau, inf
        raise ValueError(f"unknown name: {name!r}")

    if isinstance(node, ast.BinOp):
        fn = _BINOPS.get(type(node.op))
        if fn is None:
            raise ValueError(f"unsupported binary operator: {type(node.op).__name__}")
        return float(fn(_safe_eval(node.left, namespace), _safe_eval(node.right, namespace)))

    if isinstance(node, ast.UnaryOp):
        fn = _UNOPS.get(type(node.op))
        if fn is None:
            raise ValueError(f"unsupported unary operator: {type(node.op).__name__}")
        return float(fn(_safe_eval(node.operand, namespace)))

    if isinstance(node, ast.Call):
        if not (
            isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "math"
        ):
            raise ValueError("only math.* calls are allowed in enzyme expressions")
        func_name = node.func.attr
        func = _MATH_NS.get(func_name)
        if func is None or not callable(func):
            raise ValueError(f"unknown or non-callable math function: {func_name!r}")
        args = [_safe_eval(arg, namespace) for arg in node.args]
        return float(func(*args))

    raise ValueError(f"unsupported AST node type: {type(node).__name__}")


class EnzymeCompiler:
    """Mineralizes EnzymeGene definitions into CompiledEnzyme instances at startup."""

    def compile(self, gene: EnzymeGene) -> CompiledEnzyme:
        if gene.kind == "dynamic_expression":
            fn = self._dynamic_expression(gene)
        elif gene.kind == "expression":
            fn = self._expression(gene)
        elif gene.kind == "composition":
            fn = self._composition(gene)
        elif gene.kind == "python_ref":
            fn = self._python_ref(gene)
        else:
            raise ValueError(f"unknown enzyme kind: {gene.kind!r}")
        return CompiledEnzyme(
            enzyme_id=gene.enzyme_id,
            input_schema=gene.input_schema,
            output_key=gene.output_key,
            _fn=fn,
        )

    def _dynamic_expression(self, gene: EnzymeGene) -> Callable[[dict[str, Any]], dict[str, Any]]:
        """Evaluates the payload's 'expression' field as the formula (calculator bone)."""
        output_key = gene.output_key

        def _fn(payload: dict[str, Any]) -> dict[str, Any]:
            expr = str(payload.get("expression", ""))
            tree = ast.parse(expr, mode="eval")
            # Payload fields (excluding 'expression' itself) are available as variables
            ns = {k: v for k, v in payload.items() if k != "expression"}
            result = _safe_eval(tree.body, ns)
            return {output_key: result, "method": "deterministic_calculator"}

        return _fn

    def _expression(self, gene: EnzymeGene) -> Callable[[dict[str, Any]], dict[str, Any]]:
        if not gene.expression:
            raise ValueError(f"enzyme {gene.enzyme_id!r}: expression kind requires 'expression' field")
        tree_body = ast.parse(gene.expression, mode="eval").body
        output_key = gene.output_key

        def _fn(payload: dict[str, Any]) -> dict[str, Any]:
            return {output_key: _safe_eval(tree_body, payload)}

        return _fn

    def _composition(self, gene: EnzymeGene) -> Callable[[dict[str, Any]], dict[str, Any]]:
        if not gene.steps:
            raise ValueError(f"enzyme {gene.enzyme_id!r}: composition kind requires 'steps'")
        parsed_steps = [(step.output, ast.parse(step.expression, mode="eval").body) for step in gene.steps]
        output_key = gene.output_key

        def _fn(payload: dict[str, Any]) -> dict[str, Any]:
            ns: dict[str, Any] = dict(payload)
            for var_name, tree_body in parsed_steps:
                ns[var_name] = _safe_eval(tree_body, ns)
            return {output_key: ns[output_key]}

        return _fn

    def _python_ref(self, gene: EnzymeGene) -> Callable[[dict[str, Any]], dict[str, Any]]:
        if not gene.ref:
            raise ValueError(f"enzyme {gene.enzyme_id!r}: python_ref kind requires 'ref' field")
        module_path, func_name = gene.ref.rsplit(":", 1)
        module = importlib.import_module(module_path)
        func: Callable[[dict[str, Any]], dict[str, Any]] = getattr(module, func_name)

        def _fn(payload: dict[str, Any]) -> dict[str, Any]:
            return func(payload)

        return _fn

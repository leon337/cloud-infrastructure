#!/usr/bin/env python3
"""Strict YAML helpers shared by repository validators."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any, TextIO

import yaml


class StrictSafeLoader(yaml.SafeLoader):
    """SafeLoader variant that rejects ambiguous duplicate mapping keys."""


def _construct_unique_mapping(
    loader: StrictSafeLoader, node: yaml.MappingNode, deep: bool = False
) -> dict[Any, Any]:
    loader.flatten_mapping(node)
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            duplicate = key in mapping
        except TypeError as exc:
            raise yaml.constructor.ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                "found an unhashable mapping key",
                key_node.start_mark,
            ) from exc
        if duplicate:
            raise yaml.constructor.ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                f"found duplicate key {key!r}",
                key_node.start_mark,
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


StrictSafeLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


def load_all_strict(stream: str | TextIO) -> Iterable[Any]:
    return yaml.load_all(stream, Loader=StrictSafeLoader)


def load_strict(stream: str | TextIO) -> Any:
    return yaml.load(stream, Loader=StrictSafeLoader)

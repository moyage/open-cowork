from __future__ import annotations

from pathlib import Path


def load_yaml(path: str | Path):
    return loads_yaml(Path(path).read_text(encoding="utf-8"))


def dump_yaml(data) -> str:
    return _dump_node(data, 0).rstrip() + "\n"


def write_yaml(path: str | Path, data) -> None:
    Path(path).write_text(dump_yaml(data), encoding="utf-8")


def loads_yaml(text: str):
    lines = text.splitlines()
    value, index = _parse_block(lines, 0, 0)
    while index < len(lines) and not _clean(lines[index]):
        index += 1
    if index != len(lines):
        raise ValueError(f"unexpected trailing content at line {index + 1}")
    return value


def _parse_block(lines: list[str], index: int, indent: int):
    index = _skip_blank(lines, index)
    if index >= len(lines):
        return {}, index
    current_indent = _indent(lines[index])
    if current_indent < indent:
        return {}, index
    if _clean(lines[index]).startswith("- "):
        return _parse_list(lines, index, indent)
    return _parse_dict(lines, index, indent)


def _parse_dict(lines: list[str], index: int, indent: int):
    result = {}
    while index < len(lines):
        raw = lines[index]
        stripped = _clean(raw)
        if not stripped:
            index += 1
            continue
        line_indent = _indent(raw)
        if line_indent < indent:
            break
        if line_indent != indent:
            raise ValueError(f"invalid indentation at line {index + 1}")
        if stripped.startswith("- "):
            break
        key, sep, rest = stripped.partition(":")
        if not sep:
            raise ValueError(f"missing ':' at line {index + 1}")
        key = _parse_scalar(key.strip())
        rest = rest.lstrip()
        index += 1
        if rest in {">", ">-", "|", "|-"}:
            value, index = _parse_block_scalar(lines, index, indent, folded=rest.startswith(">"))
        elif rest:
            value = _parse_scalar(rest)
        else:
            value, index = _parse_nested(lines, index, indent)
        result[key] = value
    return result, index


def _parse_list(lines: list[str], index: int, indent: int):
    items = []
    while index < len(lines):
        raw = lines[index]
        stripped = _clean(raw)
        if not stripped:
            index += 1
            continue
        line_indent = _indent(raw)
        if line_indent < indent:
            break
        if line_indent != indent or not stripped.startswith("- "):
            raise ValueError(f"invalid list entry at line {index + 1}")
        body = stripped[2:].strip()
        index += 1
        if not body:
            value, index = _parse_nested(lines, index, indent)
            items.append(value)
            continue
        if ":" in body:
            key, sep, rest = body.partition(":")
            if sep and key.strip():
                item = { _parse_scalar(key.strip()): _parse_scalar(rest.lstrip()) if rest.strip() else None }
                nested, next_index = _parse_possible_nested(lines, index, indent)
                if nested is not None:
                    if not isinstance(nested, dict):
                        raise ValueError(f"list mapping continuation must be mapping at line {index + 1}")
                    for nested_key, nested_value in nested.items():
                        if nested_key in item and item[nested_key] is not None:
                            raise ValueError(f"duplicate key '{nested_key}' in list item")
                        item[nested_key] = nested_value
                    index = next_index
                items.append(item)
                continue
        items.append(_parse_scalar(body))
    return items, index


def _parse_nested(lines: list[str], index: int, indent: int):
    index = _skip_blank(lines, index)
    if index >= len(lines):
        return {}, index
    cleaned = _clean(lines[index])
    if cleaned == "{}":
        return {}, index + 1
    if cleaned == "[]":
        return [], index + 1
    next_indent = _indent(lines[index])
    if next_indent <= indent:
        return {}, index
    return _parse_block(lines, index, next_indent)


def _parse_possible_nested(lines: list[str], index: int, indent: int):
    probe = _skip_blank(lines, index)
    if probe >= len(lines):
        return None, index
    next_indent = _indent(lines[probe])
    if next_indent <= indent:
        return None, index
    return _parse_block(lines, probe, next_indent)


def _parse_block_scalar(lines: list[str], index: int, indent: int, folded: bool):
    parts = []
    while index < len(lines):
        raw = lines[index]
        if not _clean(raw):
            parts.append("")
            index += 1
            continue
        line_indent = _indent(raw)
        if line_indent <= indent:
            break
        parts.append(raw[indent + 2 :])
        index += 1
    if folded:
        return "\n".join(parts).replace("\n", " ").strip(), index
    return "\n".join(parts), index


def _parse_scalar(value: str):
    if value in {"", "null", "~"}:
        return None
    if value == "{}":
        return {}
    if value == "[]":
        return []
    if value == "true":
        return True
    if value == "false":
        return False
    if (value.startswith("'") and value.endswith("'")) or (value.startswith('"') and value.endswith('"')):
        return value[1:-1]
    if value.lstrip("-").isdigit():
        return int(value)
    return value


def _dump_node(value, indent: int) -> str:
    space = " " * indent
    if isinstance(value, dict):
        lines = []
        for key, item in value.items():
            if isinstance(item, (dict, list)):
                lines.append(f"{space}{key}:")
                lines.append(_dump_node(item, indent + 2))
            else:
                lines.append(f"{space}{key}: {_dump_scalar(item)}")
        return "\n".join(lines) if lines else f"{space}{{}}"
    if isinstance(value, list):
        lines = []
        for item in value:
            if isinstance(item, dict):
                first = True
                for key, nested in item.items():
                    prefix = f"{space}- " if first else f"{space}  "
                    if isinstance(nested, (dict, list)):
                        lines.append(f"{prefix}{key}:")
                        lines.append(_dump_node(nested, indent + 4))
                    else:
                        lines.append(f"{prefix}{key}: {_dump_scalar(nested)}")
                    first = False
                if not item:
                    lines.append(f"{space}- {{}}")
            elif isinstance(item, list):
                lines.append(f"{space}-")
                lines.append(_dump_node(item, indent + 2))
            else:
                lines.append(f"{space}- {_dump_scalar(item)}")
        return "\n".join(lines) if lines else f"{space}[]"
    return f"{space}{_dump_scalar(value)}"


def _dump_scalar(value) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    text = str(value)
    if text == "" or text != text.strip() or any(ch in text for ch in [":", "#", "[", "]", "{", "}"]):
        return repr(text)
    return text


def _clean(line: str) -> str:
    return line.strip()


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _skip_blank(lines: list[str], index: int) -> int:
    while index < len(lines) and not _clean(lines[index]):
        index += 1
    return index

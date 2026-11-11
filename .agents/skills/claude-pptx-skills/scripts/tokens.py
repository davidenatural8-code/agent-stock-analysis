#!/usr/bin/env python3
"""
Load the design layer and resolve its {aliases}.

The tokens file is layered so a value is written once and referred to everywhere
else: primitive (the only literal hex/pt/inches) -> semantic (roles like
text.primary, chart.categorical) -> type/layout/component/chart (recipes). A
string of the exact form "{a.b.c}" is an alias; anything else is a literal.

An alias is resolved by trying, in order:
    <path> from the document root      e.g. {type.caption}
    primitive.<path>                   e.g. {color.navy900}, {size.xxl}
    semantic.<path>                    e.g. {text.primary}, {chart.label}

That ordering is what lets the file stay readable ({text.primary} rather than
{semantic.text.primary}) while staying unambiguous: the first hit wins, and the
tiers don't reuse each other's top-level key names.

Only whole-string aliases are substituted. "{a} and {b}" is left alone, because
every value in this schema is a single colour/number/name, never a template.

Usage as a CLI (prints the fully resolved tree, for eyeballing or diffing):
    python tokens.py design/brand.tokens.json
    python tokens.py design/brand.tokens.json charts.bar     # merged with _base
    python tokens.py design/brand.tokens.json chart.categorical
"""
import json
import re
import sys

ALIAS_RE = re.compile(r"^\{([A-Za-z0-9_.]+)\}$")

# Tier prefixes an alias is tried against, after the document root.
SEARCH_PREFIXES = ("primitive", "semantic")


class TokenError(Exception):
    pass


def _dig(tree, path):
    """Walk a dotted path. Returns (found, value) rather than raising, because
    a miss here is normal -- it just means try the next search prefix."""
    node = tree
    for part in path.split("."):
        if not isinstance(node, dict) or part not in node:
            return False, None
        node = node[part]
    return True, node


def _lookup(tree, path):
    for candidate in (path, *(f"{p}.{path}" for p in SEARCH_PREFIXES)):
        found, value = _dig(tree, candidate)
        if found:
            return value
    raise TokenError(f"unresolved alias {{{path}}}")


def _resolve(node, tree, seen):
    """Recursively replace alias strings with their target values.

    `seen` carries the alias chain for the branch currently being resolved, so a
    cycle raises instead of recursing until the stack blows.
    """
    if isinstance(node, str):
        m = ALIAS_RE.match(node)
        if not m:
            return node
        path = m.group(1)
        if path in seen:
            chain = " -> ".join([*seen, path])
            raise TokenError(f"circular alias: {chain}")
        return _resolve(_lookup(tree, path), tree, (*seen, path))
    if isinstance(node, dict):
        return {k: _resolve(v, tree, seen) for k, v in node.items()}
    if isinstance(node, list):
        return [_resolve(v, tree, seen) for v in node]
    return node


def load(path):
    """Read a tokens file and return it with every alias resolved."""
    with open(path) as fh:
        raw = json.load(fh)
    return _resolve(raw, raw, ())


def get(tokens, path, default=None):
    """Fetch a dotted path from resolved tokens, e.g. get(t, 'type.title')."""
    found, value = _dig(tokens, path)
    if not found:
        for prefix in SEARCH_PREFIXES:
            found, value = _dig(tokens, f"{prefix}.{path}")
            if found:
                return value
        return default
    return value


def _merge(base, override):
    """Deep-merge two dicts; `override` wins. Lists replace rather than concat --
    a chart recipe that names its own palette means that palette, not both."""
    out = dict(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = v
    return out


def chart_spec(tokens, kind):
    """The styling recipe for one chart kind: charts._base with charts.<kind>
    layered on top. This is the single source of what a chart looks like, so
    callers never decide axis/gridline/label behaviour themselves.

    Note the deliberate singular/plural split: `charts.*` are these recipes,
    while `semantic.chart.*` is the colour palette they draw from.
    """
    charts = tokens.get("charts", {})
    if kind not in charts:
        known = sorted(k for k in charts if not k.startswith("_"))
        raise TokenError(f"unknown chart kind '{kind}' (have: {', '.join(known)})")
    return _merge(charts.get("_base", {}), charts[kind])


def text_spec(tokens, role):
    """The type recipe for one text role (title, body, kpi_value, ...)."""
    spec = tokens.get("type", {}).get(role)
    if spec is None:
        known = sorted(tokens.get("type", {}))
        raise TokenError(f"unknown text role '{role}' (have: {', '.join(known)})")
    return spec


def line_height_in(tokens, role):
    """How tall one line of a text role is, in inches: its size scaled by the
    role's line_height. Every block that reserves vertical space for text goes
    through here, so leading is a token rather than a constant in the code."""
    spec = text_spec(tokens, role)
    return spec["size"] / 72 * spec["line_height"]


def card_label_pad_in(tokens, component="card"):
    """Vertical space a titled card must leave above its content.

    Derived rather than stored: it is exactly the card's top padding plus one
    line of card_title plus the gap below it. Storing it separately (as an
    earlier `layout.label_pad_in` did) means two tokens describe one distance,
    so raising card_title's line_height silently leaves the chart overlapping
    the title.
    """
    comp = tokens["component"][component]
    return comp["pad_in"] + line_height_in(tokens, "card_title") + comp["title_gap_in"]


def content_area(tokens):
    """The usable rectangle below the title band, in inches, derived from layout
    tokens so no caller has to hardcode slide coordinates."""
    layout = tokens["layout"]
    canvas, margin = layout["canvas"], layout["margin"]
    top = margin["top_in"] + layout["title_band"]["h_in"]
    return {
        "x": margin["x_in"],
        "y": round(top, 3),
        "w": round(canvas["w_in"] - 2 * margin["x_in"], 3),
        "h": round(canvas["h_in"] - top - margin["bottom_in"], 3),
    }


def main():
    if len(sys.argv) not in (2, 3):
        print("Usage: tokens.py <tokens.json> [dotted.path]", file=sys.stderr)
        sys.exit(1)
    tokens = load(sys.argv[1])
    if len(sys.argv) == 3:
        path = sys.argv[2]
        # `charts.<kind>` is shown merged, since that's what consumers actually see.
        if path.startswith("charts.") and not path.startswith("charts._"):
            out = chart_spec(tokens, path.split(".", 1)[1])
        else:
            out = get(tokens, path)
            if out is None:
                raise TokenError(f"no such path: {path}")
    else:
        out = tokens
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    try:
        main()
    except TokenError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

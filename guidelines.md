# PyFS Commenting Guidelines

All comments in this codebase follow the rules below. Consistency matters
more than cleverness — when in doubt, write less.

---

## 1. Module Docstrings

Every `.py` file gets a **one-line** docstring at the top unless the
file-level contract is genuinely non-obvious, in which case a short
paragraph is acceptable.

```python
"""Software bus singleton — routes messages between nodes."""
```

Do not write module docstrings that merely restate the filename.

---

## 2. Class Docstrings

One-liner that says **what** the class is and **how** to use it.
Expand to a short paragraph only when the usage contract is subtle.

```python
class FSBus:
    """Singleton software bus. pub() is non-blocking; subscribers are isolated."""
```

Avoid:
- "This class is responsible for…"
- "This class provides…"
- Long narratives about internal implementation details.

---

## 3. Method / Function Docstrings

Use a **one-liner** for any method whose purpose, arguments, and return
value are evident from its signature and name.

```python
def stop(self) -> None:
    """Signal the dispatch thread to exit and join it."""
```

Expand only when the behaviour is non-obvious or has a documented
side-effect that a caller must know about.

Do **not** include `Args:` / `Returns:` sections for self-evident
signatures — they add noise without value.

---

## 4. Inline Comments

- One space after `#`, then a capital letter if it's a sentence, lowercase
  otherwise.
- Explain **why**, never **what** (the code shows what).
- Keep them short — one line maximum per comment block.

```python
self._sock.settimeout(1.0)  # allows the recv loop to check the stop event
```

---

## 5. Section Separators

Use **exactly** this style for visual section breaks inside a class:

```
# ── Section Name ──────────────────────────────────────────────────────
```

Rules:
- Leading `# `, then `── `, then the section name, then a space, then `─`
  characters to reach **column 72**.
- Use `─` (U+2500, BOX DRAWINGS LIGHT HORIZONTAL), never `-` or `=`.
- Keep separator text concise — two or three words.
- Only use section separators when a class is long enough that scrolling
  otherwise makes the layout hard to follow (roughly 60+ lines).

---

## 6. Type Annotation Comments on Tuples

When a module-level tuple table has non-obvious field ordering, annotate
the type signature instead of writing a free-form comment:

```python
_TASK_TABLE: list[tuple[int, Mid]] = [...]   # (rate_hz, mid)
```

The inline comment is acceptable here because the positional meaning cannot
be expressed in the type alone.

---

## 7. Log Calls

Always use `%`-style formatting in log calls — **never** f-strings:

```python
# correct
self.log.info("node %s started", self.name)

# wrong
self.log.info(f"node {self.name} started")
```

This allows the logging layer to skip string interpolation when the log
level is filtered out.

---

## 8. What Not to Write

Avoid the following patterns — they are signs of AI-generated filler:

- "This method handles…"
- "We then…"
- Restating the function name in prose ("The `stop` method stops the node.")
- Listing every step the code takes ("First we do X, then we do Y")
- Commenting on every single line
- Redundant `noqa` explanations that duplicate what the comment already says

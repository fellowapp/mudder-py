# mudder-py

This library is a port of [fasiha/mudderjs][1] to Python.

From the original readme:

> Generate lexicographically-spaced strings between two strings from
> pre-defined alphabets.

[1]: https://github.com/fasiha/mudderjs


## Example

Usage is nearly identical to the original:

```python
from mudder import SymbolTable


hex_ = SymbolTable('0123456789abcdef')
hexstrings = hex_.mudder('ffff', 'fe0f', num_strings=3)
print(hexstrings)
# ['ff8', 'ff', 'fe8']
```

# mudder-py

[![GitHub Workflow Status (main)](https://img.shields.io/github/actions/workflow/status/fellowapp/mudder-py/ci.yml?branch=main&style=flat)][main CI]
[![PyPI](https://img.shields.io/pypi/v/mudder?style=flat)][package]
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/mudder?style=flat)][package]
[![License](https://img.shields.io/pypi/l/mudder.svg?style=flat)](https://github.com/fellowapp/mudder-py/blob/master/LICENSE.md)
[![Fellow Careers](https://img.shields.io/badge/fellow.app-hiring-576cf7.svg?style=flat)](https://fellow.app/careers/)

[main CI]: https://github.com/fellowapp/mudder-py/actions?query=workflow%3ACI+branch%3Amain
[package]: https://pypi.org/project/mudder/

This library is a port of [fasiha/mudderjs][1] to Python.

From the original readme:

> Generate lexicographically-spaced strings between two strings from pre-defined
> alphabets.

This technique is also known as
[_fractional indexing_](https://observablehq.com/@dgreensp/implementing-fractional-indexing).

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

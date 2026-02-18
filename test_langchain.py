#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test script to check langchain module structure"""

try:
    from langchain_core.globals import set_debug
    print("OK: langchain_core.globals exists")
except ImportError as e:
    print(f"FAIL: langchain_core.globals: {e}")

try:
    from langchain.globals import set_debug
    print("OK: langchain.globals exists")
except ImportError as e:
    print(f"FAIL: langchain.globals: {e}")

# Check what's in langchain
try:
    import langchain
    print(f"\nlangchain module contents: {[x for x in dir(langchain) if not x.startswith('_')]}")
except Exception as e:
    print(f"Error importing langchain: {e}")

# Check what's in langchain_core
try:
    import langchain_core
    print(f"\nlangchain_core module contents: {[x for x in dir(langchain_core) if not x.startswith('_')]}")
except Exception as e:
    print(f"Error importing langchain_core: {e}")


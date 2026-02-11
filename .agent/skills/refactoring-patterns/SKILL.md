---
name: refactoring-patterns
description: Patterns and techniques for improving the design of existing code without changing its observable behavior.
allowed-tools: Read, Write, Edit, Glob, Grep
---

# Refactoring Patterns

> **"Any fool can write code that a computer can understand. Good programmers write code that humans can understand."** — Martin Fowler

---

## The Refactoring Workflow

1. **Check tests:** Ensure the code is covered by tests.
2. **Small steps:** Make one small change at a time.
3. **Verify:** Run tests after every change.
4. **Commit:** Keep a clean history of refactoring steps.

---

## Core Principles

| Principle | Description |
|-----------|-------------|
| **Observable Behavior** | Refactoring never adds features or fixes bugs. |
| **Boy Scout Rule** | Leave the code cleaner than you found it. |
| **Code Smells** | Identify signs that indicate refactoring is needed (Long Method, Duplicate Code, etc.). |

---

## Essential Patterns

### 1. Composing Methods
| Pattern | Action |
|---------|--------|
| **Extract Method** | Turn a fragment of code into its own method. |
| **Inline Method** | Put a method's body into its callers if it's too simple. |
| **Replace Temp with Query** | Replace a local variable with a function call. |
| **Introduce Explaining Variable** | Use a descriptive variable for complex expressions. |

### 2. Moving Features between Objects
| Pattern | Action |
|---------|--------|
| **Move Method** | Move a method to the class it uses most. |
| **Move Field** | Move a field to the class it uses most. |
| **Extract Class** | Split a class that does too much. |
| **Hide Delegate** | Encapsulate relationships between objects. |

### 3. Simplifying Conditional Expressions
| Pattern | Action |
|---------|--------|
| **Decompose Conditional** | Extract methods from `if/then/else` parts. |
| **Consolidate Conditional** | Merge conditions that lead to the same result. |
| **Guard Clauses** | Use early returns to simplify nested logic. |
| **Replace Conditional with Polymorphism** | Use subclasses/interfaces instead of `switch/case`. |

### 4. Organizing Data
| Pattern | Action |
|---------|--------|
| **Replace Magic Number** | Use named constants. |
| **Encapsulate Field** | Make fields private and use getters/setters. |
| **Replace Array with Object** | Use objects for structured data. |

---

## Common Code Smells (When to Refactor)

- **Long Method:** Methods longer than 20 lines.
- **Large Class:** Classes that handle multiple responsibilities.
- **Duplicated Code:** Similar logic in multiple places.
- **Shotgun Surgery:** One change requires many small changes in different classes.
- **Feature Envy:** A method that seems more interested in another class than its own.

---

## Safety Rules

1. **Don't mix Refactoring with Logic changes.**
2. **If you break the tests, revert immediately.**
3. **Use automated tools (IDE refactoring) when available.**

---

> **Remember:** Refactoring is a continuous process, not a one-time project.

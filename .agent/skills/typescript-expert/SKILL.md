---
name: typescript-expert
description: Advanced TypeScript patterns, type safety, configuration, and performance. 
allowed-tools: Read, Write, Edit, Glob, Grep
---

# TypeScript Expert

> **"Explicit is better than implicit. Type safety is not optional."**

---

## Core Principles

1. **No `any`:** Avoid `any` at all costs. Use `unknown` if you don't know the type.
2. **Strict Mode:** Always favor `strict: true` in `tsconfig.json`.
3. **Inference:** Let TypeScript infer simple types, but be explicit for public boundaries.
4. **Zod/Validation:** Trust no input. Validate at the boundaries.

---

## Advanced Patterns

### 1. Utility Types

- `Partial<T>`, `Required<T>`, `Readonly<T>`
- `Pick<T, K>`, `Omit<T, K>`
- `Record<K, T>`
- `ReturnType<T>`, `Parameters<T>`

### 2. Type Guards & Predicates

```typescript
function isUser(obj: any): obj is User {
  return obj && typeof obj.id === 'string';
}
```

### 3. Discriminated Unions

```typescript
type Result = 
  | { status: 'success'; data: string }
  | { status: 'error'; message: string };
```

### 4. Generics

```typescript
function wrapInArray<T>(item: T): T[] {
  return [item];
}
```

---

## tsconfig.json Best Practices

```json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "exactOptionalPropertyTypes": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true
  }
}
```

---

## Anti-Patterns

- ❌ Using `any`
- ❌ Non-null assertions (`!`) when not absolutely necessary
- ❌ Over-complicating types (aim for readability)
- ❌ Missing Zod/Validation at API boundaries

---

> **Remember:** Types are documentation that never goes out of sync.

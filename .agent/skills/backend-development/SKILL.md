---
name: backend-development
description: Backend systems architecture, server implementation, and infrastructure.
allowed-tools: Read, Write, Edit, Glob, Grep
---

# Backend Development

> **The Backbone of Scalable Applications.**

---

## Core Pillars

1. **API Design:** REST, GraphQL, tRPC.
2. **Database:** Modeling, Migrations, ACID, Performance.
3. **Security:** Auth, Sanitization, CORS, Rate-limiting.
4. **Performance:** Caching, Async Jobs, Optimization.

---

## Platform Routing

| Platform / Language | Skill to Use |
|---------------------|--------------|
| Node.js / Express / NestJS | `@[skills/nodejs-best-practices]` |
| Python / FastAPI / Django | `@[skills/python-patterns]` |
| Rust / Axum / Actix | `@[skills/rust-pro]` |
| API Design Patterns | `@[skills/api-patterns]` |
| Database Design | `@[skills/database-design]` |

---

## Essential Checklist

- [ ] **Validation:** All inputs sanitized and validated.
- [ ] **Error Handling:** Centralized error management, consistent responses.
- [ ] **Logging:** Structured logging for debugging and monitoring.
- [ ] **Configuration:** Environment variables, no hardcoded secrets.
- [ ] **Tests:** Unit and Integration tests for business logic.

---

## Performance & Scalability

- **Caching:** Redis, In-memory.
- **Microservices:** Only if complexity warrants it.
- **Serverless:** For event-driven or low-volume tasks.
- **Monitoring:** Prometheus, Grafana, ELK Stack.

---

> **Remember:** A backend should be predictable, observable, and secure.

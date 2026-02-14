# 🤖 Claude Development Guide - Sankhya Super Agent

> **Guia de desenvolvimento para Claude ao trabalhar neste projeto.**
> Este documento organiza as 42 skills disponíveis em `.agent/skills/` para uso durante o desenvolvimento do Sankhya Super Agent.

---

## 📋 Índice

- [Regras Críticas](#-regras-críticas)
- [Workflow de Desenvolvimento](#-workflow-de-desenvolvimento)
- [Skills por Categoria](#-skills-por-categoria)
- [Quando Usar Cada Skill](#-quando-usar-cada-skill)
- [Scripts de Validação](#-scripts-de-validação)
- [Referência Rápida](#-referência-rápida)

---

## 🔴 Regras Críticas

### 1. Clean Code (SEMPRE)
**Localização:** `.agent/skills/clean-code/SKILL.md`

- ✅ Código conciso, direto, sem over-engineering
- ✅ Funções pequenas (max 20 linhas, idealmente 5-10)
- ✅ Nomes revelam intenção: `userCount` não `n`
- ✅ Um nível de abstração por função
- ✅ Guard clauses ao invés de nesting profundo
- ❌ **NUNCA** comentários óbvios
- ❌ **NUNCA** criar helpers para one-liners
- ❌ **NUNCA** "First we import..." - só escreva código

**Antes de editar QUALQUER arquivo:**
1. Quem importa este arquivo? (podem quebrar)
2. O que este arquivo importa? (mudanças de interface)
3. Que testes cobrem isso? (podem falhar)
4. É componente compartilhado? (múltiplos lugares afetados)

### 2. Socratic Gate (MANDATÓRIO para features complexas)
**Localização:** `.agent/skills/brainstorming/SKILL.md`

**QUANDO DISPARAR:**
- "Build/Create/Make [coisa]" sem detalhes
- Feature complexa ou arquitetural
- Requisitos vagos ou ambíguos

**PROCESSO OBRIGATÓRIO:**
1. 🛑 **PARAR** - NÃO começar a codar
2. ❓ **PERGUNTAR** - Mínimo 3 perguntas:
   - 🎯 **Propósito:** Que problema você está resolvendo?
   - 👥 **Usuários:** Quem vai usar isso?
   - 📦 **Escopo:** Must-have vs nice-to-have?
3. ⏳ **AGUARDAR** - Esperar resposta antes de prosseguir

**Formato de Perguntas:**
```markdown
### [P0/P1/P2] **[PONTO DE DECISÃO]**

**Pergunta:** [Pergunta clara]

**Por que isso importa:**
- [Consequência arquitetural]
- [Afeta: custo/complexidade/timeline/escala]

**Opções:**
| Opção | Prós | Contras | Melhor Para |
|-------|------|---------|-------------|
| A | [+] | [-] | [Caso de uso] |

**Se não especificado:** [Default + justificativa]
```

### 3. Self-Check Antes de Completar (MANDATÓRIO)

**Antes de dizer "tarefa completa", verificar:**

| Check | Pergunta |
|-------|----------|
| ✅ **Meta atingida?** | Fiz exatamente o que o usuário pediu? |
| ✅ **Arquivos editados?** | Modifiquei todos os arquivos necessários? |
| ✅ **Código funciona?** | Testei/verifiquei a mudança? |
| ✅ **Sem erros?** | Lint e TypeScript passam? |
| ✅ **Nada esquecido?** | Algum edge case perdido? |

🔴 **REGRA:** Se QUALQUER check falhar, corrija antes de completar.

---

## 🔄 Workflow de Desenvolvimento

```
┌─────────────────────────────────────────────────────────────┐
│ 1. ENTENDER (brainstorming)                                 │
│    └─ Requisitos vagos? → Socratic Gate                     │
│    └─ Complexo? → 3+ perguntas antes de começar             │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. PLANEJAR (architecture, plan-writing)                    │
│    └─ Decisões arquiteturais → architecture                 │
│    └─ Trade-offs → Documentar ADRs                          │
│    └─ Alternativas mais simples consideradas?               │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. IMPLEMENTAR (clean-code + skill específica)              │
│    Backend → backend-development + api-patterns             │
│    Frontend → frontend-design + react-best-practices        │
│    Mobile → mobile-design                                   │
│    Database → database-design                               │
│    Security → security-hardening + vulnerability-scanner    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. TESTAR (testing-patterns, tdd-workflow)                  │
│    └─ Testes unitários para lógica                          │
│    └─ Testes de integração para APIs/DB                     │
│    └─ E2E para fluxos críticos                              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. VALIDAR (scripts + lint-and-validate)                    │
│    └─ Rodar script de validação do role                     │
│    └─ Lint e type checking                                  │
│    └─ Security scan se relevante                            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. REVISAR (code-review-checklist)                          │
│    └─ Self-review antes de completar                        │
│    └─ Todos os checks verdes?                               │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 7. DOCUMENTAR (documentation-templates)                     │
│    └─ Atualizar README se necessário                        │
│    └─ Comentários apenas onde lógica não é auto-evidente    │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Skills por Categoria

### 💻 Desenvolvimento

| Skill | Quando Usar | Localização |
|-------|-------------|-------------|
| **clean-code** | **SEMPRE** - Base para todo código | `.agent/skills/clean-code/` |
| **app-builder** | Criar aplicações full-stack do zero | `.agent/skills/app-builder/` |
| **backend-development** | Arquitetura backend, servers, infra | `.agent/skills/backend-development/` |
| **frontend-design** | Design de UI/UX, componentes, layouts | `.agent/skills/frontend-design/` |
| **python-patterns** | Código Python, padrões pythonic | `.agent/skills/python-patterns/` |
| **typescript-expert** | TypeScript avançado, types complexos | `.agent/skills/typescript-expert/` |
| **nodejs-best-practices** | Node.js, Express, async patterns | `.agent/skills/nodejs-best-practices/` |
| **rust-pro** | Desenvolvimento Rust | `.agent/skills/rust-pro/` |

### 🧪 Testing & Quality

| Skill | Quando Usar | Localização |
|-------|-------------|-------------|
| **testing-patterns** | Escrever testes (unit, integration, E2E) | `.agent/skills/testing-patterns/` |
| **tdd-workflow** | Test-Driven Development | `.agent/skills/tdd-workflow/` |
| **webapp-testing** | Testes de aplicações web (Playwright, etc) | `.agent/skills/webapp-testing/` |
| **code-review-checklist** | Code review, verificação de qualidade | `.agent/skills/code-review-checklist/` |
| **lint-and-validate** | Linting, formatação, type checking | `.agent/skills/lint-and-validate/` |

### 🎨 Design & UX

| Skill | Quando Usar | Localização |
|-------|-------------|-------------|
| **mobile-design** | Design mobile (iOS/Android), touch UX | `.agent/skills/mobile-design/` |
| **web-design-guidelines** | Guidelines de web design | `.agent/skills/web-design-guidelines/` |
| **tailwind-patterns** | Padrões Tailwind CSS | `.agent/skills/tailwind-patterns/` |
| **i18n-localization** | Internacionalização, traduções | `.agent/skills/i18n-localization/` |

### 🔒 Segurança

| Skill | Quando Usar | Localização |
|-------|-------------|-------------|
| **vulnerability-scanner** | Scan de vulnerabilidades, security audit | `.agent/skills/vulnerability-scanner/` |
| **security-hardening** | Hardening de infra, OWASP, defesa em profundidade | `.agent/skills/security-hardening/` |
| **red-team-tactics** | Pentest, táticas de ataque (autorizado) | `.agent/skills/red-team-tactics/` |

### 🏗️ Arquitetura & Patterns

| Skill | Quando Usar | Localização |
|-------|-------------|-------------|
| **architecture** | Decisões arquiteturais, ADRs, trade-offs | `.agent/skills/architecture/` |
| **api-patterns** | REST vs GraphQL vs tRPC, design de APIs | `.agent/skills/api-patterns/` |
| **refactoring-patterns** | Refactoring de código existente | `.agent/skills/refactoring-patterns/` |
| **mcp-builder** | Construir MCP servers/tools | `.agent/skills/mcp-builder/` |
| **database-design** | Schema design, indexing, ORM selection | `.agent/skills/database-design/` |

### 🚀 DevOps & Deploy

| Skill | Quando Usar | Localização |
|-------|-------------|-------------|
| **deployment-procedures** | Deploy em produção, rollback, CI/CD | `.agent/skills/deployment-procedures/` |
| **server-management** | Gerenciamento de servidores | `.agent/skills/server-management/` |
| **bash-linux** | Scripts Bash/Linux, terminal operations | `.agent/skills/bash-linux/` |
| **powershell-windows** | PowerShell, automação Windows | `.agent/skills/powershell-windows/` |

### 🛠️ Utilities & Process

| Skill | Quando Usar | Localização |
|-------|-------------|-------------|
| **brainstorming** | **MANDATÓRIO** para features complexas | `.agent/skills/brainstorming/` |
| **systematic-debugging** | Debug complexo, root cause analysis | `.agent/skills/systematic-debugging/` |
| **performance-profiling** | Otimização de performance, profiling | `.agent/skills/performance-profiling/` |
| **documentation-templates** | Templates de docs, README, API docs | `.agent/skills/documentation-templates/` |
| **behavioral-modes** | Modos operacionais (implement, debug, review) | `.agent/skills/behavioral-modes/` |
| **intelligent-routing** | Roteamento de tarefas entre agentes | `.agent/skills/intelligent-routing/` |
| **parallel-agents** | Execução paralela de agentes | `.agent/skills/parallel-agents/` |
| **plan-writing** | Escrever planos de implementação | `.agent/skills/plan-writing/` |

### 🎮 Especializadas

| Skill | Quando Usar | Localização |
|-------|-------------|-------------|
| **game-development** | Desenvolvimento de games | `.agent/skills/game-development/` |
| **geo-fundamentals** | Features geoespaciais | `.agent/skills/geo-fundamentals/` |
| **seo-fundamentals** | SEO, otimização para buscadores | `.agent/skills/seo-fundamentals/` |

---

## 📖 Quando Usar Cada Skill

### Cenário: Adicionando Nova Feature

```
1. brainstorming → Entender requisitos (3+ perguntas)
2. architecture → Se envolve decisões arquiteturais
3. clean-code → SEMPRE ao escrever código
4. [skill específica] → backend-development, frontend-design, etc
5. testing-patterns → Escrever testes
6. lint-and-validate → Rodar linters
7. code-review-checklist → Self-review
```

### Cenário: Corrigindo Bug

```
1. systematic-debugging → Reproduzir, isolar, entender, corrigir
2. clean-code → Ao escrever a correção
3. testing-patterns → Adicionar teste de regressão
4. [script de validação] → Rodar script do role
```

### Cenário: Refactoring

```
1. refactoring-patterns → Padrões de refactoring
2. clean-code → Manter código limpo
3. testing-patterns → Garantir testes cobrem código
4. code-review-checklist → Verificar se quebrou algo
```

### Cenário: Decisão Arquitetural

```
1. architecture → Framework de decisão, ADRs
2. api-patterns → Se envolve APIs
3. database-design → Se envolve database
4. brainstorming → Se requisitos não estão claros
```

### Cenário: Security Review

```
1. vulnerability-scanner → Scan automatizado
2. security-hardening → OWASP, hardening
3. code-review-checklist → Verificação manual
```

### Cenário: Performance Issue

```
1. systematic-debugging → Identificar gargalo
2. performance-profiling → Profiling, métricas
3. refactoring-patterns → Otimizar código
4. testing-patterns → Testes de performance
```

---

## 🔬 Scripts de Validação

**REGRA:** Cada role roda APENAS seus próprios scripts após completar trabalho.

| Role | Script | Comando |
|------|--------|---------|
| **frontend-specialist** | UX Audit | `python .agent/skills/frontend-design/scripts/ux_audit.py .` |
| **frontend-specialist** | A11y Check | `python .agent/skills/frontend-design/scripts/accessibility_checker.py .` |
| **backend-specialist** | API Validator | `python .agent/skills/api-patterns/scripts/api_validator.py .` |
| **mobile-developer** | Mobile Audit | `python .agent/skills/mobile-design/scripts/mobile_audit.py .` |
| **database-architect** | Schema Validate | `python .agent/skills/database-design/scripts/schema_validator.py .` |
| **security-auditor** | Security Scan | `python .agent/skills/vulnerability-scanner/scripts/security_scan.py .` |
| **seo-specialist** | SEO Check | `python .agent/skills/seo-fundamentals/scripts/seo_checker.py .` |
| **seo-specialist** | GEO Check | `python .agent/skills/geo-fundamentals/scripts/geo_checker.py .` |
| **performance-optimizer** | Lighthouse | `python .agent/skills/performance-profiling/scripts/lighthouse_audit.py <url>` |
| **test-engineer** | Test Runner | `python .agent/skills/testing-patterns/scripts/test_runner.py .` |
| **test-engineer** | Playwright | `python .agent/skills/webapp-testing/scripts/playwright_runner.py <url>` |
| **Any role** | Lint Check | `python .agent/skills/lint-and-validate/scripts/lint_runner.py .` |
| **Any role** | Type Coverage | `python .agent/skills/lint-and-validate/scripts/type_coverage.py .` |
| **Any role** | i18n Check | `python .agent/skills/i18n-localization/scripts/i18n_checker.py .` |

### 🔴 Tratamento de Saída de Scripts (LER → RESUMIR → PERGUNTAR)

**Ao rodar um script de validação, você DEVE:**

1. **Rodar o script** e capturar TODA a saída
2. **Parsear a saída** - identificar erros, warnings, passes
3. **Resumir para o usuário** neste formato:

```markdown
## Resultados do Script: [nome_script.py]

### ❌ Erros Encontrados (X itens)
- [Arquivo:Linha] Descrição do erro 1
- [Arquivo:Linha] Descrição do erro 2

### ⚠️ Warnings (Y itens)
- [Arquivo:Linha] Descrição do warning

### ✅ Passou (Z itens)
- Check 1 passou
- Check 2 passou

**Devo corrigir os X erros?**
```

4. **Aguardar confirmação do usuário** antes de corrigir
5. **Após corrigir** → Re-rodar script para confirmar

> 🔴 **VIOLAÇÃO:** Rodar script e ignorar saída = Tarefa FALHADA.
> 🔴 **VIOLAÇÃO:** Auto-corrigir sem perguntar = Não permitido.
> 🔴 **REGRA:** Sempre LER saída → RESUMIR → PERGUNTAR → então corrigir.

---

## ⚡ Referência Rápida

### Debugging
```
Phase 1: Reproduce → Passos confiáveis
Phase 2: Isolate → Quando começou? O que mudou?
Phase 3: Understand → 5 Whys, root cause
Phase 4: Fix & Verify → Corrigir, testar, adicionar regression test
```

### Testing Pyramid
```
        /\          E2E (Poucos)
       /  \         Fluxos críticos
      /----\
     /      \       Integration (Alguns)
    /--------\      API, DB queries
   /          \
  /------------\    Unit (Muitos)
                    Funções, classes
```

### Princípios Arquiteturais
```
1. Requisitos dirigem arquitetura
2. Trade-offs informam decisões
3. ADRs capturam justificativa
4. Simplicidade é sofisticação
5. Adicionar complexidade é fácil, remover é difícil
```

### Code Smells
```
❌ Método longo (>20 linhas)
❌ Classe grande (múltiplas responsabilidades)
❌ Código duplicado
❌ Magic numbers
❌ Nesting profundo (>2 níveis)
❌ Comentários óbvios
❌ God functions
```

### Security Checklist
```
✅ Injection → Sanitize inputs, parameterized queries
✅ Auth → MFA, strong hashing (Argon2, bcrypt)
✅ Sensitive Data → Encrypt at rest/transit (TLS)
✅ XSS/CSRF → CSP, CSRF tokens
✅ Rate-limiting → DoS/brute-force protection
✅ Dependencies → Regular security scans
```

---

## 🎓 Skills Relacionadas

Algumas skills referenciam outras. Siga os links:

```
architecture
  └─> database-design (Schema design)
  └─> api-patterns (API design)
  └─> deployment-procedures (Deploy architecture)

security-hardening
  └─> vulnerability-scanner (Scanning)
  └─> red-team-tactics (Pentest)
  └─> api-patterns (API security)

frontend-design
  └─> mobile-design (Mobile-specific)
  └─> web-design-guidelines (Web-specific)
  └─> tailwind-patterns (Tailwind CSS)

testing-patterns
  └─> tdd-workflow (TDD process)
  └─> webapp-testing (E2E testing)
```

---

## 📚 Onde Ler Mais

Cada skill em `.agent/skills/[skill-name]/` contém:

- `SKILL.md` - Guia principal da skill
- Arquivos adicionais (patterns, examples, checklists)
- `scripts/` - Scripts de validação (quando aplicável)

**Regra de Leitura Seletiva:**
> Leia APENAS arquivos relevantes para a tarefa atual. Não precisa ler tudo.

---

## 🚨 Lembretes Finais

1. **Clean Code é CRÍTICO** - Aplique sempre
2. **Socratic Gate é MANDATÓRIO** - Para features complexas
3. **Self-Check antes de completar** - Todos os checks verdes
4. **Rodar scripts de validação** - Resumir → Perguntar → Corrigir
5. **Testes são documentação** - Se alguém não entende o código pelos testes, reescreva
6. **Segurança é processo** - Não é produto
7. **Refactoring nunca adiciona features** - Apenas melhora design
8. **Simplicidade > Complexidade** - Sempre começar simples

---

**Este guia é um mapa vivo. Consulte as skills individuais em `.agent/skills/` para detalhes completos.**

🤖 _Happy Coding!_ 🚀

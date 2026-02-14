"""
Development Skills Orchestrator

Analisa conversas e ativa automaticamente skills de desenvolvimento
quando o contexto é sobre melhorar/desenvolver o sistema (não demandas Sankhya).
"""

import os
import re
from typing import List, Dict, Optional, Tuple
from pathlib import Path


class DevelopmentOrchestrator:
    """
    Orquestrador inteligente que:
    1. Distingue entre demandas Sankhya vs desenvolvimento do sistema
    2. Analisa intent e ativa skills apropriadas
    3. Injeta regras críticas no system prompt
    """

    def __init__(self):
        self.skills_dir = Path(__file__).parent.parent.parent.parent / ".agent" / "skills"
        self.skills_cache = {}
        self._load_core_skills()

    def _load_core_skills(self):
        """Carrega skills críticas que devem estar sempre ativas."""
        core_skills = [
            'clean-code',
            'brainstorming',
            'systematic-debugging',
            'testing-patterns',
            'architecture'
        ]

        for skill_name in core_skills:
            skill_path = self.skills_dir / skill_name / "SKILL.md"
            if skill_path.exists():
                self.skills_cache[skill_name] = self._read_skill(skill_path)

    def _read_skill(self, skill_path: Path) -> Dict[str, str]:
        """Lê um SKILL.md e extrai metadados e conteúdo."""
        try:
            content = skill_path.read_text(encoding='utf-8')

            # Extrair frontmatter (entre --- e ---)
            frontmatter_match = re.match(r'^---\n(.*?)\n---\n(.*)', content, re.DOTALL)
            if not frontmatter_match:
                return {'content': content}

            frontmatter_text = frontmatter_match.group(1)
            body = frontmatter_match.group(2)

            # Parse frontmatter (YAML simples)
            metadata = {}
            for line in frontmatter_text.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    metadata[key.strip()] = value.strip()

            metadata['content'] = body
            return metadata

        except Exception as e:
            return {'error': str(e)}

    def detect_context(self, user_message: str) -> Tuple[str, float]:
        """
        Detecta se a mensagem é sobre:
        - 'sankhya_runtime': Demanda para usar o sistema Sankhya
        - 'system_development': Desenvolver/melhorar o próprio sistema

        Retorna: (contexto, confiança)
        """
        message_lower = user_message.lower()

        # Padrões que indicam DESENVOLVIMENTO do sistema
        dev_patterns = [
            # Verbos de desenvolvimento
            r'\b(adicione|adicionar|crie|criar|implemente|implementar|desenvolva|desenvolver)\b.*\b(feature|funcionalidade|skill|ferramenta|tool|módulo|sistema)\b',
            r'\b(melhore|melhorar|otimize|otimizar|refatore|refatorar|corrija|corrigir)\b.*\b(código|sistema|agente|agent)\b',

            # Referências ao sistema
            r'\b(agent_client|mcp_server|orchestrator|skills|\.agent/)\b',
            r'\b(this (system|code|project|agent))\b',

            # Desenvolvimento explícito
            r'\b(código|code|implementação|implementation|arquitetura|architecture)\b',
            r'\b(teste|test|validação|validation|script)\b.*\b(criar|adicionar|melhorar)\b',

            # Meta-desenvolvimento
            r'\b(incorporar|integrar|adicionar|criar)\b.*\b(skill|agent|orquestrador|orchestrator)\b',
            r'\b(desenvolvimento|development|programação|programming)\b',
        ]

        # Padrões que indicam USO do Sankhya (runtime)
        sankhya_patterns = [
            # Verbos de consulta/ação no Sankhya
            r'\b(mostre|mostrar|liste|listar|consulte|consultar|busque|buscar|veja|ver)\b.*\b(estoque|produto|nota|pedido|parceiro|vendas)\b',
            r'\b(qual|quais|quanto|quantos)\b.*\b(estoque|saldo|custo|preço|vendas)\b',

            # Entidades Sankhya
            r'\b(tgfpro|tgfest|tgfcab|tgfite|tgfpar|tgfcus|codprod|nunota|codparc)\b',
            r'\b(produto|estoque|nota fiscal|pedido|parceiro|cliente|fornecedor)\b.*\b(código|numero|data)\b',

            # Ações de negócio
            r'\b(cadastre|cadastrar|atualize|atualizar|delete|deletar)\b.*\b(produto|parceiro|nota)\b',
            r'\b(relatório|dashboard|gráfico|chart)\b.*\b(vendas|estoque|compras)\b',

            # SQL/Query direto
            r'\b(select|from|where)\b.*\b(tgf|tsi)\w+\b',
            r'\b(execute|executar|rode|rodar)\b.*\b(sql|query|consulta)\b',
        ]

        # Contar matches
        dev_score = sum(1 for pattern in dev_patterns if re.search(pattern, message_lower))
        sankhya_score = sum(1 for pattern in sankhya_patterns if re.search(pattern, message_lower))

        # Decisão
        if dev_score > sankhya_score:
            confidence = min(0.95, 0.5 + (dev_score * 0.15))
            return 'system_development', confidence
        elif sankhya_score > dev_score:
            confidence = min(0.95, 0.5 + (sankhya_score * 0.15))
            return 'sankhya_runtime', confidence
        else:
            # Empate ou ambos zero - padrão: runtime
            return 'sankhya_runtime', 0.3

    def analyze_development_intent(self, user_message: str) -> List[str]:
        """
        Analisa a mensagem e retorna skills de desenvolvimento a ativar.

        Só é chamado quando detect_context() retorna 'system_development'.
        """
        message_lower = user_message.lower()
        active_skills = ['clean-code']  # SEMPRE ativo

        # Mapeamento de padrões → skills
        skill_patterns = {
            'brainstorming': [
                r'\b(adicione|crie|implemente|desenvolva)\b.*\b(feature|funcionalidade|sistema|dashboard|módulo|relatório)\b',
                r'\b(build|create|make|add)\b.*\b(feature|system|dashboard|module|report)\b',
                r'\b(build|create|make)\b.*\b(without|sem)\b.*\b(detail|detalhe)\b',
                r'\b(complexo|complex|vago|vague|unclear)\b',
                r'\b(nova|novo|new)\b.*\b(feature|funcionalidade|dashboard)\b',
            ],
            'architecture': [
                r'\b(arquitetura|architecture|decisão|decision|adr)\b',
                r'\b(design|desenhe|estrutura|structure)\b.*\b(sistema|system)\b',
                r'\b(pattern|padrão|approach|abordagem)\b',
            ],
            'systematic-debugging': [
                r'\b(bug|erro|error|problema|issue|não funciona|not working|broken)\b',
                r'\b(debug|debugar|investigar|investigate)\b',
                r'\b(corrija|corrigir|fix|resolver)\b',
            ],
            'testing-patterns': [
                r'\b(teste|test|testing|testes)\b',
                r'\b(unit|integration|e2e|coverage)\b',
                r'\b(jest|vitest|pytest|playwright)\b',
            ],
            'refactoring-patterns': [
                r'\b(refatore|refactor|refactoring|melhore|improve|otimize|optimize)\b.*\b(código|code)\b',
                r'\b(clean|limpe|organize|reorganize)\b',
            ],
            'security-hardening': [
                r'\b(segurança|security|vulnerabilidade|vulnerability)\b',
                r'\b(owasp|injection|xss|csrf|auth)\b',
                r'\b(harden|hardening|proteja|protect)\b',
            ],
            'api-patterns': [
                r'\b(api|endpoint|route|rest|graphql|trpc)\b',
                r'\b(request|response|http|status)\b',
            ],
            'database-design': [
                r'\b(database|banco|schema|migration|tabela|table)\b',
                r'\b(sql|query|index|orm|prisma)\b',
            ],
            'performance-profiling': [
                r'\b(performance|performace|lento|slow|otimize|optimize)\b',
                r'\b(profile|profiling|benchmark|speed|velocidade)\b',
            ],
            'frontend-design': [
                r'\b(ui|ux|interface|componente|component|layout)\b',
                r'\b(react|vue|design|estilo|style)\b',
            ],
            'backend-development': [
                r'\b(backend|server|api|endpoint|serviço|service)\b',
                r'\b(express|fastapi|node|python)\b',
            ],
            'deployment-procedures': [
                r'\b(deploy|deployment|ci/cd|docker|kubernetes)\b',
                r'\b(production|produção|release)\b',
            ],
            'documentation-templates': [
                r'\b(documentação|documentation|readme|docs)\b',
                r'\b(documente|document|escreva.*doc)\b',
            ],
        }

        # Checar cada skill
        for skill, patterns in skill_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    if skill not in active_skills:
                        active_skills.append(skill)
                    break  # Já adicionou essa skill

        return active_skills

    def get_core_skills_context(self) -> str:
        """
        Retorna o contexto das skills críticas que devem estar sempre ativas
        durante desenvolvimento do sistema.
        """
        context_parts = []

        # Clean Code (CRITICAL)
        if 'clean-code' in self.skills_cache:
            context_parts.append("""
🔴 **CLEAN CODE (CRITICAL - ALWAYS ACTIVE)**

CORE PRINCIPLES:
- SRP: Single Responsibility - cada função/classe faz UMA coisa
- DRY: Don't Repeat Yourself - extrair duplicatas
- KISS: Keep It Simple - solução mais simples que funciona
- YAGNI: You Aren't Gonna Need It - não construir features não usadas

NAMING RULES:
- Variables: Revela intenção: `userCount` não `n`
- Functions: Verbo + substantivo: `getUserById()` não `user()`
- Booleans: Forma de pergunta: `isActive`, `hasPermission`
- Constants: SCREAMING_SNAKE: `MAX_RETRY_COUNT`

FUNCTION RULES:
- Max 20 linhas, idealmente 5-10
- Uma coisa, faz bem
- Um nível de abstração
- Max 3 argumentos
- Sem side effects inesperados

CODE STRUCTURE:
- Guard clauses (early returns)
- Flat > Nested (max 2 níveis)
- Composição de funções pequenas

ANTI-PATTERNS (DON'T):
❌ Comentários óbvios
❌ Helper para one-liner
❌ "First we import..." - só escreva código
❌ Deep nesting - use guard clauses
❌ Magic numbers - use constantes nomeadas

BEFORE EDITING ANY FILE:
1. Quem importa este arquivo? (podem quebrar)
2. O que este arquivo importa? (mudanças de interface)
3. Que testes cobrem isso? (podem falhar)
4. É componente compartilhado? (múltiplos lugares afetados)
""")

        # Brainstorming / Socratic Gate
        if 'brainstorming' in self.skills_cache:
            context_parts.append("""
🛑 **SOCRATIC GATE (MANDATORY para features complexas)**

WHEN TO TRIGGER:
- "Build/Create/Make [coisa]" sem detalhes
- Feature complexa ou arquitetural
- Requisitos vagos ou ambíguos
- Update/change request sem especificação

MANDATORY PROCESS:
1. 🛑 PARAR - NÃO começar a codar
2. ❓ PERGUNTAR - Mínimo 3 perguntas:
   - 🎯 Propósito: Que problema você está resolvendo?
   - 👥 Usuários: Quem vai usar isso?
   - 📦 Escopo: Must-have vs nice-to-have?
3. ⏳ AGUARDAR - Esperar resposta antes de prosseguir

QUESTION FORMAT:
### [P0/P1/P2] **[DECISION POINT]**
**Question:** [Clear question]
**Why This Matters:** [Architectural consequence]
**Options:** [Table with pros/cons]
**If Not Specified:** [Default + rationale]
""")

        # Systematic Debugging
        if 'systematic-debugging' in self.skills_cache:
            context_parts.append("""
🔬 **SYSTEMATIC DEBUGGING (Para bugs/erros)**

4-PHASE PROCESS:
Phase 1: Reproduce → Passos confiáveis para reproduzir
Phase 2: Isolate → Quando começou? O que mudou? Menor caso?
Phase 3: Understand → 5 Whys, encontrar root cause
Phase 4: Fix & Verify → Corrigir, testar, adicionar regression test

ANTI-PATTERNS:
❌ Mudanças aleatórias - "Maybe if I change this..."
❌ Ignorar evidências - "That can't be the cause"
❌ Assumir sem prova - "It must be X"
❌ Não reproduzir primeiro - Fixing blindly
❌ Parar em sintomas - Not finding root cause
""")

        # Testing Patterns
        if 'testing-patterns' in self.skills_cache:
            context_parts.append("""
🧪 **TESTING PATTERNS (Ao criar testes)**

TESTING PYRAMID:
        /\\          E2E (Poucos) - Fluxos críticos
       /  \\
      /----\\        Integration (Alguns) - API, DB
     /      \\
    /--------\\      Unit (Muitos) - Funções, classes

AAA PATTERN:
- Arrange: Set up test data
- Act: Execute code under test
- Assert: Verify outcome

PRINCIPLES:
- Fast (< 100ms cada)
- Isolated (sem deps externas)
- Repeatable (mesmo resultado sempre)
- Self-checking (sem verificação manual)
""")

        # Architecture
        if 'architecture' in self.skills_cache:
            context_parts.append("""
🏗️ **ARCHITECTURE (Decisões arquiteturais)**

CORE PRINCIPLE:
"Simplicidade é sofisticação"
- Começar simples
- Adicionar complexidade APENAS quando provado necessário
- Pode sempre adicionar patterns depois
- Remover complexidade é MUITO mais difícil que adicionar

VALIDATION CHECKLIST:
- [ ] Requisitos claramente entendidos
- [ ] Constraints identificados
- [ ] Cada decisão tem análise de trade-offs
- [ ] Alternativas mais simples consideradas
- [ ] ADRs escritos para decisões significativas
""")

        return "\n".join(context_parts)

    def get_skills_context(self, skill_names: List[str]) -> str:
        """
        Retorna o contexto combinado de múltiplas skills.
        Usado quando skills específicas são ativadas baseado no intent.
        """
        context_parts = []

        for skill_name in skill_names:
            if skill_name in self.skills_cache:
                skill_data = self.skills_cache[skill_name]
                name = skill_data.get('name', skill_name)
                description = skill_data.get('description', '')

                context_parts.append(f"\n📚 **{name.upper()}**")
                if description:
                    context_parts.append(f"   {description}")
            else:
                # Tentar carregar skill se não estiver em cache
                skill_path = self.skills_dir / skill_name / "SKILL.md"
                if skill_path.exists():
                    skill_data = self._read_skill(skill_path)
                    self.skills_cache[skill_name] = skill_data

                    name = skill_data.get('name', skill_name)
                    description = skill_data.get('description', '')

                    context_parts.append(f"\n📚 **{name.upper()}**")
                    if description:
                        context_parts.append(f"   {description}")

        return "\n".join(context_parts)

    def should_activate_development_mode(self, user_message: str) -> Tuple[bool, str, List[str]]:
        """
        Decide se deve ativar modo desenvolvimento e quais skills usar.

        Returns:
            (ativar_modo_dev, contexto, skills_ativas)
        """
        context, confidence = self.detect_context(user_message)

        if context == 'system_development' and confidence > 0.5:
            active_skills = self.analyze_development_intent(user_message)
            return True, context, active_skills
        else:
            return False, context, []


# Singleton global
_orchestrator_instance = None

def get_orchestrator() -> DevelopmentOrchestrator:
    """Retorna instância singleton do orchestrator."""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = DevelopmentOrchestrator()
    return _orchestrator_instance

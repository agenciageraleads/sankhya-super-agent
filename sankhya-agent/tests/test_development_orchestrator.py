"""
Testes para o Development Orchestrator

Verifica se o orquestrador detecta corretamente o contexto
(Sankhya runtime vs System development) e ativa as skills certas.
"""

import sys
from pathlib import Path

# Adicionar path do projeto
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mcp_server.skills.development_orchestrator import get_orchestrator


def test_context_detection():
    """Testa detecção de contexto."""
    orchestrator = get_orchestrator()

    test_cases = [
        # Sankhya Runtime
        ("mostre o estoque do produto 20", "sankhya_runtime"),
        ("liste as vendas de hoje", "sankhya_runtime"),
        ("busque o parceiro código 100", "sankhya_runtime"),
        ("execute select * from tgfpro where rownum <= 5", "sankhya_runtime"),
        ("qual o saldo do produto X?", "sankhya_runtime"),
        ("consulte as notas fiscais do mês", "sankhya_runtime"),

        # System Development
        ("adicione uma nova skill para relatórios", "system_development"),
        ("crie uma feature de dashboard", "system_development"),
        ("melhore o código do orchestrator", "system_development"),
        ("corrija o bug no agent_client.py", "system_development"),
        ("refatore o mcp_server", "system_development"),
        ("implemente testes para as skills", "system_development"),
        ("desenvolva um novo módulo de BI", "system_development"),
        ("otimize o código do sankhya adapter", "system_development"),
    ]

    print("=" * 70)
    print("TESTE DE DETECÇÃO DE CONTEXTO")
    print("=" * 70)

    correct = 0
    total = len(test_cases)

    for message, expected_context in test_cases:
        context, confidence = orchestrator.detect_context(message)
        is_correct = context == expected_context

        status = "✅" if is_correct else "❌"
        if is_correct:
            correct += 1

        print(f"\n{status} Mensagem: {message}")
        print(f"   Esperado: {expected_context}")
        print(f"   Detectado: {context} (confiança: {confidence:.2f})")

    print("\n" + "=" * 70)
    print(f"RESULTADO: {correct}/{total} corretos ({100*correct/total:.1f}%)")
    print("=" * 70)

    return correct == total


def test_skill_activation():
    """Testa ativação de skills baseado no intent."""
    orchestrator = get_orchestrator()

    test_cases = [
        # Bug fix → debugging + clean-code + testing
        ("corrija o erro no login", ["systematic-debugging", "clean-code"]),

        # Nova feature → brainstorming + architecture + clean-code
        ("adicione um dashboard de vendas", ["brainstorming", "clean-code"]),

        # Refactoring → refactoring-patterns + clean-code
        ("refatore o código do orchestrator", ["refactoring-patterns", "clean-code"]),

        # Testes → testing-patterns + clean-code
        ("crie testes unitários para as skills", ["testing-patterns", "clean-code"]),

        # Segurança → security-hardening + clean-code
        ("revise a segurança da API", ["security-hardening", "clean-code"]),
    ]

    print("\n" + "=" * 70)
    print("TESTE DE ATIVAÇÃO DE SKILLS")
    print("=" * 70)

    for message, expected_skills in test_cases:
        active_skills = orchestrator.analyze_development_intent(message)

        # Verificar se todas as skills esperadas estão presentes
        all_present = all(skill in active_skills for skill in expected_skills)
        status = "✅" if all_present else "❌"

        print(f"\n{status} Mensagem: {message}")
        print(f"   Esperado: {expected_skills}")
        print(f"   Ativadas: {active_skills}")

    print("\n" + "=" * 70)


def test_full_workflow():
    """Testa workflow completo: detectar contexto + ativar skills."""
    orchestrator = get_orchestrator()

    test_messages = [
        "mostre o estoque do produto 20",  # Runtime - não deve ativar dev mode
        "adicione uma feature de relatórios customizados",  # Dev - deve ativar
        "corrija o bug no agent_client.py",  # Dev - deve ativar debugging
    ]

    print("\n" + "=" * 70)
    print("TESTE DE WORKFLOW COMPLETO")
    print("=" * 70)

    for message in test_messages:
        print(f"\n📝 Mensagem: {message}")

        activate_dev, context, skills = orchestrator.should_activate_development_mode(message)

        print(f"   Contexto: {context}")
        print(f"   Ativar Dev Mode: {activate_dev}")
        if activate_dev:
            print(f"   Skills Ativas: {skills}")

            # Mostrar contexto das skills
            if skills:
                skills_context = orchestrator.get_skills_context(skills[:2])  # Primeiras 2
                print(f"\n   📚 Preview do Contexto:")
                preview = skills_context[:200] + "..." if len(skills_context) > 200 else skills_context
                print(f"   {preview}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    print("\n🧪 TESTANDO DEVELOPMENT ORCHESTRATOR\n")

    # Rodar testes
    test_context_detection()
    test_skill_activation()
    test_full_workflow()

    print("\n✅ Testes concluídos!\n")

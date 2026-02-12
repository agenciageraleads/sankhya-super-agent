# Project Plan: Procurement Skills Integration

**Goal:** Formally register the newly developed Procurement Skills (Direct Giro Analysis, Excel Reporting, Feedback Learning) into the Orchestrator's workflow to enable autonomous execution.

## Phase 1: Skill Registry & Automation  

Currently, the logic exists in standalone Python scripts. The Orchestrator needs "Triggers" to know *when* and *how* to use them.

- [ ] **Create Workflow: Daily Procurement Report**
  - File: `.agent/workflows/procurement-daily.md`
  - Trigger: "Gerar relatório de compras", "Analisar giro", "Sugestão de compras"
  - Action: Run `python scripts/generate_procurement_excel.py`
  - Output: Path to the generated Excel file.

- [ ] **Create Workflow: Feedback Learning**
  - File: `.agent/workflows/procurement-feedback.md`
  - Trigger: "Processar retorno", "Ler feedback de compras", "Aprender com planilha"
  - Action: Run `python scripts/learn_from_feedback.py <file_path>`
  - Context: Should look for the most recent or user-specified Excel file.

## Phase 2: Logic Integration (Sankhya Adapter)

Ensure the core logic in `SankhyaProcurementService` is robust and accessible.

- [ ] **Verify `get_giro_data` Integration**
  - Ensure the method handles connection errors gracefully.
  - Validate parameters (Company IDs 1 & 5 hardcoded vs parameterized).
- [ ] **Verify `learn_from_feedback` Persistence**
  - Ensure `feedback_rules.json` is loaded correctly by the `generate_procurement_excel.py` script (Closing the loop).
  - **Crucial:** The current `generate_procurement_excel.py` needs to *read* these rules to modify its suggestions. (This is currently missing!).

## Phase 3: Orchestrator Awareness (System Prompts)

Update the operational context to make the Agent aware of these new capabilities.

- [ ] **Update `docs/active_skills.md` (or equivalent)**
  - Add entry for "Procurement Intelligence".
  - Describe the "Excel -> WhatsApp -> Feedback -> Learn" cycle.

## Phase 4: Validation

- [ ] Run the `/procurement-daily` workflow via command.
- [ ] Validate that the Orchestrator correctly identifies the intent from natural language (e.g., "Como estamos de estoque hoje?").

---

## Current Status (Pre-Plan)

- **Scripts:** Ready (`generate_procurement_excel.py`, `learn_from_feedback.py`).
- **Data Access:** Ready (`queries_giro_direct.sql`, `sankhya_adapter.py`).
- **Missing:**
    1. The "Read" part of the feedback loop (Excel generator doesn't yet use the learned rules).
    2. Formal workflow definitions for the Orchestrator.

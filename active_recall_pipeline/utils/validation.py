from __future__ import annotations

import json
from dataclasses import dataclass, field


@dataclass
class ValidationResult:
    passed: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class StageValidator:

    def _parse_json_output(self, raw: str) -> tuple[list | dict | None, str | None]:
        """Parse JSON from AI output. Strip markdown fences if present."""
        if not raw or not isinstance(raw, str):
            return None, "Output is not a string"
        raw = raw.strip()
        if raw.startswith("```json"):
            raw = raw[7:]
        if raw.startswith("```"):
            raw = raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()
        try:
            return json.loads(raw), None
        except json.JSONDecodeError as e:
            return None, f"Invalid JSON: {e}"

    def _check_required_keys(self, item: dict, required: set[str], item_index: int) -> list[str]:
        if not isinstance(item, dict):
            return [f"Item {item_index}: not a dictionary"]
        missing = required - set(item.keys())
        return [f"Item {item_index}: missing key '{k}'" for k in sorted(missing)]

    # ─────────────────────────────────────────────────────────────────
    # SURVEY
    # ─────────────────────────────────────────────────────────────────
    def validate_survey(self, output: list, context: dict) -> ValidationResult:
        """Validate SURVEY output. Only fails on unparseable structure."""
        errors = []
        warnings = []

        if not isinstance(output, list):
            return ValidationResult(passed=False, errors=["Output is not a list"])

        if not output:
            warnings.append("Output list is empty")
            return ValidationResult(passed=True, warnings=warnings)

        for section in output:
            if not isinstance(section, dict):
                errors.append("Section is not a dict — cannot parse")
                continue
            section_id = section.get("section_id", "?")
            concepts = section.get("concepts", [])
            if not isinstance(concepts, list):
                errors.append(f"Section {section_id}: concepts is not a list")
                continue
            if len(concepts) < 10:
                warnings.append(
                    f"Section {section_id}: only {len(concepts)} concepts extracted"
                )
            for concept in concepts:
                if isinstance(concept, str) and len(concept) > 300:
                    warnings.append(
                        f"Section {section_id}: concept exceeds 300 chars — "
                        f"may be a sentence not a noun phrase"
                    )

        return ValidationResult(passed=len(errors) == 0, errors=errors, warnings=warnings)

    # ─────────────────────────────────────────────────────────────────
    # CONSOLIDATE
    # ─────────────────────────────────────────────────────────────────
    def validate_consolidate(self, output: list, context: dict) -> ValidationResult:
        """Validate and auto-coerce CONSOLIDATE output."""
        errors = []
        warnings = []

        if not isinstance(output, list):
            return ValidationResult(passed=False, errors=["Output is not a list"])

        if not output:
            warnings.append("Output list is empty")
            return ValidationResult(passed=True, warnings=warnings)

        all_ids = []

        for section in output:
            if not isinstance(section, dict):
                errors.append("Section is not a dict")
                continue
            section_id = section.get("section_id", "?")
            concepts = section.get("concepts", [])
            if not isinstance(concepts, list):
                errors.append(f"Section {section_id}: concepts is not a list")
                continue

            for idx, item in enumerate(concepts):
                if not isinstance(item, dict):
                    warnings.append(f"Section {section_id} item {idx}: not a dict — skipped")
                    continue

                # AUTO-COERCE: id string → int
                if "id" in item:
                    if not isinstance(item["id"], int):
                        try:
                            item["id"] = int(item["id"])
                            warnings.append(f"Section {section_id} item {idx}: coerced id to int")
                        except (ValueError, TypeError):
                            errors.append(f"Section {section_id} item {idx}: id cannot be cast to int")
                            continue
                else:
                    errors.append(f"Section {section_id} item {idx}: missing key 'id'")
                    continue

                # AUTO-COERCE: missing type → STANDALONE
                if "type" not in item:
                    item["type"] = "STANDALONE"
                    warnings.append(f"Section {section_id} item {idx}: missing type, defaulted to STANDALONE")

                # AUTO-COERCE: missing children → []
                if "children" not in item:
                    item["children"] = []

                # AUTO-COERCE: STANDALONE with children → clear children
                if item["type"] == "STANDALONE" and item.get("children"):
                    item["children"] = []
                    warnings.append(f"Section {section_id} item {idx}: cleared children from STANDALONE")

                # AUTO-COERCE: CLUSTER with < 2 children → STANDALONE
                if item["type"] == "CLUSTER" and len(item.get("children", [])) < 2:
                    item["type"] = "STANDALONE"
                    item["children"] = []
                    warnings.append(
                        f"Section {section_id} item {idx}: "
                        f"CLUSTER had {len(item.get('children', []))} children — converted to STANDALONE"
                    )

                if "text" not in item or not str(item.get("text", "")).strip():
                    warnings.append(f"Section {section_id} item {idx}: empty text")

                all_ids.append(item["id"])

        # AUTO-COERCE: duplicate ids → renumber globally
        if len(all_ids) != len(set(all_ids)):
            warnings.append("Duplicate concept ids found — renumbering globally")
            counter = 1
            for section in output:
                if not isinstance(section, dict):
                    continue
                for item in section.get("concepts", []):
                    if isinstance(item, dict) and "id" in item:
                        item["id"] = counter
                        counter += 1

        return ValidationResult(passed=len(errors) == 0, errors=errors, warnings=warnings)

    # ─────────────────────────────────────────────────────────────────
    # TIER
    # ─────────────────────────────────────────────────────────────────
    def validate_tier(self, output: list, context: dict) -> ValidationResult:
        """Validate TIER output. Count/id mismatches are warnings only."""
        errors = []
        warnings = []

        if not isinstance(output, list):
            return ValidationResult(passed=False, errors=["Output is not a list"])

        if not output:
            warnings.append("Output list is empty")
            return ValidationResult(passed=True, warnings=warnings)

        consolidate_ids = set(context.get("consolidate_ids", []))
        consolidate_count = context.get("consolidate_count", 0)
        seen_ids = set()

        for section in output:
            if not isinstance(section, dict):
                errors.append("Section is not a dict")
                continue
            concepts = section.get("concepts", [])
            if not isinstance(concepts, list):
                errors.append(f"Section {section.get('section_id','?')}: concepts is not a list")
                continue
            for item in concepts:
                if isinstance(item, dict) and "id" in item and isinstance(item["id"], int):
                    seen_ids.add(item["id"])

        if consolidate_count and len(seen_ids) != consolidate_count:
            warnings.append(
                f"Tier has {len(seen_ids)} concepts, consolidate had {consolidate_count} — "
                f"missing concepts will default to MEDIUM tier"
            )

        if consolidate_ids:
            missing = consolidate_ids - seen_ids
            if missing:
                warnings.append(
                    f"Missing ids from consolidate: {sorted(missing)} — "
                    f"will default to MEDIUM tier"
                )

        return ValidationResult(passed=len(errors) == 0, errors=errors, warnings=warnings)

    # ─────────────────────────────────────────────────────────────────
    # EXCAVATE
    # ─────────────────────────────────────────────────────────────────
    def validate_excavate(self, output: list, context: dict) -> ValidationResult:
        """Validate EXCAVATE output. Missing concepts are warnings only."""
        errors = []
        warnings = []

        if not isinstance(output, list):
            return ValidationResult(passed=False, errors=["Output is not a list"])

        if not output:
            warnings.append("Output list is empty")
            return ValidationResult(passed=True, warnings=warnings)

        non_simple_ids = set(context.get("non_simple_ids", []))
        seen_concept_ids = set()

        for section in output:
            if not isinstance(section, dict):
                errors.append("Section is not a dict")
                continue
            concepts = section.get("concepts", [])
            if not isinstance(concepts, list):
                errors.append(f"Section {section.get('section_id','?')}: concepts is not a list")
                continue
            for item in concepts:
                if isinstance(item, dict) and "id" in item and isinstance(item["id"], int):
                    seen_concept_ids.add(item["id"])

        if non_simple_ids:
            missing = non_simple_ids - seen_concept_ids
            if missing:
                warnings.append(
                    f"Missing non-simple concept ids: {sorted(missing)} — "
                    f"these concepts will still get questions from original inventory"
                )

        return ValidationResult(passed=len(errors) == 0, errors=errors, warnings=warnings)

    # ─────────────────────────────────────────────────────────────────
    # FORGE
    # ─────────────────────────────────────────────────────────────────
    def validate_forge(self, output: list, context: dict) -> ValidationResult:
        """Validate FORGE output. Auto-remove unusable questions. No floor check."""
        errors = []
        warnings = []

        if not isinstance(output, list):
            return ValidationResult(passed=False, errors=["Output is not a list"])

        if not output:
            warnings.append("Output list is empty — AUDIT will identify all gaps for PATCH")
            return ValidationResult(passed=True, warnings=warnings)

        required_keys = {
            "q_id", "inventory_id", "layer", "format",
            "difficulty", "question", "answer", "tags"
        }
        seen_q_ids = set()
        items_to_remove = []

        for idx, item in enumerate(output):
            if not isinstance(item, dict):
                items_to_remove.append(idx)
                warnings.append(f"Item {idx}: not a dict — removed")
                continue

            # ERROR: missing inventory_id — cannot map to concept
            if "inventory_id" not in item:
                items_to_remove.append(idx)
                warnings.append(f"Item {idx}: missing inventory_id — removed")
                continue

            # ERROR: empty question or answer — unusable card
            if not item.get("question") or not str(item.get("question", "")).strip():
                items_to_remove.append(idx)
                warnings.append(f"Item {idx}: empty question — removed")
                continue

            if not item.get("answer") or not str(item.get("answer", "")).strip():
                items_to_remove.append(idx)
                warnings.append(f"Item {idx}: empty answer — removed")
                continue

            # WARNINGS for cosmetic issues
            missing = required_keys - set(item.keys())
            for k in sorted(missing):
                warnings.append(f"Item {idx}: missing key '{k}'")

            if "q_id" in item:
                if item["q_id"] in seen_q_ids:
                    warnings.append(f"Item {idx}: duplicate q_id '{item['q_id']}'")
                seen_q_ids.add(item["q_id"])

            if "tags" in item and "Inventory::" not in str(item["tags"]):
                warnings.append(f"Item {idx}: tags missing 'Inventory::' — AUDIT may miss this concept")

        # Remove unusable items in reverse order
        for idx in reversed(items_to_remove):
            output.pop(idx)

        if items_to_remove:
            warnings.append(f"Removed {len(items_to_remove)} unusable questions")

        return ValidationResult(passed=True, errors=[], warnings=warnings)

    # ─────────────────────────────────────────────────────────────────
    # PATCH
    # ─────────────────────────────────────────────────────────────────
    def validate_patch(self, output: list, context: dict) -> ValidationResult:
        """Validate PATCH output. Same philosophy as FORGE."""
        errors = []
        warnings = []

        if not isinstance(output, list):
            return ValidationResult(passed=False, errors=["Output is not a list"])

        if not output:
            warnings.append("Output list is empty")
            return ValidationResult(passed=True, warnings=warnings)

        seen_q_ids = set()
        items_to_remove = []

        for idx, item in enumerate(output):
            if not isinstance(item, dict):
                items_to_remove.append(idx)
                warnings.append(f"Item {idx}: not a dict — removed")
                continue

            if "inventory_id" not in item:
                items_to_remove.append(idx)
                warnings.append(f"Item {idx}: missing inventory_id — removed")
                continue

            if not item.get("question") or not str(item.get("question", "")).strip():
                items_to_remove.append(idx)
                warnings.append(f"Item {idx}: empty question — removed")
                continue

            if not item.get("answer") or not str(item.get("answer", "")).strip():
                items_to_remove.append(idx)
                warnings.append(f"Item {idx}: empty answer — removed")
                continue

            if "q_id" in item:
                if item["q_id"] in seen_q_ids:
                    warnings.append(f"Item {idx}: duplicate q_id '{item['q_id']}'")
                seen_q_ids.add(item["q_id"])

            if "tags" in item and "Inventory::" not in str(item["tags"]):
                warnings.append(f"Item {idx}: tags missing 'Inventory::'")

        for idx in reversed(items_to_remove):
            output.pop(idx)

        if items_to_remove:
            warnings.append(f"Removed {len(items_to_remove)} unusable questions")

        return ValidationResult(passed=True, errors=[], warnings=warnings)

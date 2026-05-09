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
        """Parse JSON from AI output. Strip ```json fences if present.
        Returns (parsed_object, None) on success.
        Returns (None, error_message) on failure.
        """
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
            parsed = json.loads(raw)
            return parsed, None
        except json.JSONDecodeError as e:
            return None, f"Invalid JSON: {e}"

    def _check_required_keys(self, item: dict, required: set[str], item_index: int) -> list[str]:
        """Return list of error strings for missing keys."""
        if not isinstance(item, dict):
            return [f"Item {item_index}: not a dictionary"]

        errors = []
        missing = required - set(item.keys())
        for key in sorted(missing):
            errors.append(f"Item {item_index}: missing key '{key}'")

        return errors

    def validate_survey(self, output: list, context: dict) -> ValidationResult:
        """Validate SURVEY output: list of section dicts."""
        errors = []
        warnings = []

        if not isinstance(output, list):
            return ValidationResult(passed=False, errors=["Output is not a list"])
        if not output:
            return ValidationResult(passed=False, errors=["Output list is empty"])

        total_concepts = 0

        for section in output:
            if not isinstance(section, dict):
                errors.append("Section is not a dict")
                continue
            section_id = section.get("section_id", "?")
            concepts = section.get("concepts", [])
            if not isinstance(concepts, list):
                errors.append(f"Section {section_id}: concepts is not a list")
                continue
            if len(concepts) < 10:
                errors.append(
                    f"Section {section_id}: only {len(concepts)} concepts, minimum is 10"
                )
            for concept in concepts:
                if not isinstance(concept, str):
                    continue
                total_concepts += 1
                if len(concept) > 300:
                    errors.append(
                        f"Section {section_id}: concept exceeds 300 chars"
                    )

        return ValidationResult(
            passed=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def validate_consolidate(self, output: list, context: dict) -> ValidationResult:
        """Validate CONSOLIDATE output: list of section dicts."""
        errors = []
        warnings = []

        if not isinstance(output, list):
            return ValidationResult(passed=False, errors=["Output is not a list"])
        if not output:
            return ValidationResult(passed=False, errors=["Output list is empty"])

        required_keys = {"id", "text", "type", "children"}
        valid_types = {"STANDALONE", "CLUSTER"}
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
                item_errors = self._check_required_keys(item, required_keys, idx)
                errors.extend([f"Section {section_id}: {e}" for e in item_errors])
                if not isinstance(item, dict):
                    continue
                if "type" in item and item["type"] not in valid_types:
                    errors.append(
                        f"Section {section_id} item {idx}: "
                        f"type='{item['type']}' must be STANDALONE or CLUSTER"
                    )
                if "id" in item:
                    if not isinstance(item["id"], int):
                        errors.append(
                            f"Section {section_id} item {idx}: id is not an integer"
                        )
                    else:
                        all_ids.append(item["id"])
                if "text" in item and not str(item["text"]).strip():
                    errors.append(f"Section {section_id} item {idx}: text is empty")
                if "type" in item and "children" in item:
                    children = item["children"]
                    if not isinstance(children, list):
                        errors.append(
                            f"Section {section_id} item {idx}: children is not a list"
                        )
                    elif item["type"] == "STANDALONE" and children:
                        errors.append(
                            f"Section {section_id} item {idx}: "
                            "STANDALONE must have empty children"
                        )
                    elif item["type"] == "CLUSTER" and len(children) < 2:
                        errors.append(
                            f"Section {section_id} item {idx}: "
                            f"CLUSTER has {len(children)} children, minimum is 2"
                        )

        if len(all_ids) != len(set(all_ids)):
            errors.append("Duplicate concept ids found across sections")

        return ValidationResult(
            passed=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def validate_tier(self, output: list, context: dict) -> ValidationResult:
        """Validate TIER output: list of section dicts."""
        errors = []
        warnings = []

        if not isinstance(output, list):
            return ValidationResult(passed=False, errors=["Output is not a list"])
        if not output:
            return ValidationResult(passed=False, errors=["Output list is empty"])

        valid_tiers = {"SIMPLE", "MEDIUM", "COMPLEX"}
        consolidate_ids = set(context.get("consolidate_ids", []))
        consolidate_count = context.get("consolidate_count", 0)
        seen_ids = set()

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
                    continue
                if "tier" in item and item["tier"] not in valid_tiers:
                    errors.append(
                        f"Section {section_id} item {idx}: "
                        f"tier='{item['tier']}' must be SIMPLE, MEDIUM, or COMPLEX"
                    )
                if "id" in item and isinstance(item["id"], int):
                    seen_ids.add(item["id"])

        total_tiered = len(seen_ids)
        if consolidate_count and total_tiered != consolidate_count:
            errors.append(
                f"Count mismatch: tier has {total_tiered} concepts, "
                f"consolidate has {consolidate_count}"
            )

        if consolidate_ids:
            missing = consolidate_ids - seen_ids
            if missing:
                errors.append(f"Missing ids from consolidate: {sorted(missing)}")

        return ValidationResult(
            passed=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def validate_excavate(self, output: list, context: dict) -> ValidationResult:
        """Validate EXCAVATE output: list of section dicts."""
        errors = []
        warnings = []

        if not isinstance(output, list):
            return ValidationResult(passed=False, errors=["Output is not a list"])
        if not output:
            return ValidationResult(passed=False, errors=["Output list is empty"])

        non_simple_ids = set(context.get("non_simple_ids", []))
        seen_concept_ids = set()

        for section in output:
            if not isinstance(section, dict):
                errors.append("Section is not a dict")
                continue
            section_id = section.get("section_id", "?")
            concepts = section.get("concepts", [])
            if not isinstance(concepts, list):
                errors.append(f"Section {section_id}: concepts is not a list")
                continue
            for item in concepts:
                if not isinstance(item, dict):
                    continue
                if "id" in item and isinstance(item["id"], int):
                    seen_concept_ids.add(item["id"])

        if non_simple_ids:
            missing = non_simple_ids - seen_concept_ids
            if missing:
                errors.append(
                    f"Missing non-simple concept ids in excavated output: "
                    f"{sorted(missing)}"
                )

        return ValidationResult(
            passed=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def validate_forge(self, output: list, context: dict) -> ValidationResult:
        """Validate FORGE output: generated MCQ questions."""
        errors = []
        warnings = []

        if not isinstance(output, list):
            return ValidationResult(passed=False, errors=["Output is not a list"])

        if not output:
            return ValidationResult(passed=False, errors=["Output list is empty"])

        concept_count = context.get("concept_count", 0)

        # Calculate minimum floor
        if concept_count < 20:
            min_floor = 50
        elif concept_count < 40:
            min_floor = 75
        elif concept_count < 60:
            min_floor = 100
        else:
            min_floor = 120

        if len(output) < min_floor:
            errors.append(
                f"Only {len(output)} questions generated, minimum is {min_floor} "
                f"(concept_count={concept_count})"
            )

        required_keys = {
            "q_id", "inventory_id", "layer", "format", "difficulty",
            "question", "answer", "tags"
        }
        valid_layers = {
            "Foundation", "Surface", "Reasoning", "Boundary",
            "Ordering", "Lineage"
        }
        valid_formats = {"Direct", "Statement", "Ordering"}
        valid_difficulties = {"Easy", "Medium", "Hard"}
        seen_q_ids = set()
        duplicate_q_ids = []

        for idx, item in enumerate(output):
            item_errors = self._check_required_keys(item, required_keys, idx)
            errors.extend(item_errors)

            if not isinstance(item, dict):
                continue

            if "layer" in item and item["layer"] not in valid_layers:
                errors.append(f"Item {idx}: layer='{item['layer']}' not in {valid_layers}")

            if "format" in item and item["format"] not in valid_formats:
                errors.append(f"Item {idx}: format='{item['format']}' not in {valid_formats}")

            if "difficulty" in item and item["difficulty"] not in valid_difficulties:
                errors.append(
                    f"Item {idx}: difficulty='{item['difficulty']}' not in {valid_difficulties}"
                )

            if "q_id" in item:
                q_id = item["q_id"]
                if q_id in seen_q_ids:
                    duplicate_q_ids.append(q_id)
                seen_q_ids.add(q_id)

            if "question" in item:
                question = item["question"]
                if not question or not str(question).strip():
                    errors.append(f"Item {idx}: question is empty or whitespace only")

            if "answer" in item:
                answer = item["answer"]
                if not answer or not str(answer).strip():
                    errors.append(f"Item {idx}: answer is empty or whitespace only")

            if "tags" in item:
                tags = str(item["tags"])
                if "Inventory::" not in tags:
                    errors.append(f"Item {idx}: tags missing 'Inventory::' substring")

        if duplicate_q_ids:
            errors.append(f"Duplicate q_ids found: {duplicate_q_ids}")

        return ValidationResult(
            passed=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def validate_patch(self, output: list, context: dict) -> ValidationResult:
        """Validate PATCH output: gap-fill questions."""
        errors = []
        warnings = []

        if not isinstance(output, list):
            return ValidationResult(passed=False, errors=["Output is not a list"])

        if not output:
            return ValidationResult(passed=False, errors=["Output list is empty"])

        gap_ids = set(context.get("gap_ids", []))
        existing_q_ids = set(context.get("existing_q_ids", []))

        required_keys = {
            "q_id", "inventory_id", "layer", "format", "difficulty",
            "question", "answer", "tags"
        }
        valid_layers = {
            "Foundation", "Surface", "Reasoning", "Boundary",
            "Ordering", "Lineage"
        }
        valid_formats = {"Direct", "Statement", "Ordering"}
        valid_difficulties = {"Easy", "Medium", "Hard"}
        seen_q_ids = set()
        invalid_inventory_ids = []
        duplicate_q_ids = []
        conflicting_q_ids = []

        for idx, item in enumerate(output):
            item_errors = self._check_required_keys(item, required_keys, idx)
            errors.extend(item_errors)

            if not isinstance(item, dict):
                continue

            if "layer" in item and item["layer"] not in valid_layers:
                errors.append(f"Item {idx}: layer='{item['layer']}' not in {valid_layers}")

            if "format" in item and item["format"] not in valid_formats:
                errors.append(f"Item {idx}: format='{item['format']}' not in {valid_formats}")

            if "difficulty" in item and item["difficulty"] not in valid_difficulties:
                errors.append(
                    f"Item {idx}: difficulty='{item['difficulty']}' not in {valid_difficulties}"
                )

            if "tags" in item:
                tags = str(item["tags"])
                if "Inventory::" not in tags:
                    errors.append(f"Item {idx}: tags missing 'Inventory::'")
                if "GapFill::true" not in tags:
                    errors.append(f"Item {idx}: tags missing 'GapFill::true'")

            if "inventory_id" in item:
                inv_id = item["inventory_id"]
                if gap_ids and inv_id not in gap_ids:
                    invalid_inventory_ids.append(inv_id)

            if "q_id" in item:
                q_id = item["q_id"]
                if q_id in seen_q_ids:
                    duplicate_q_ids.append(q_id)
                if q_id in existing_q_ids:
                    conflicting_q_ids.append(q_id)
                seen_q_ids.add(q_id)

            if "question" in item:
                question = item["question"]
                if not question or not str(question).strip():
                    errors.append(f"Item {idx}: question is empty or whitespace only")

            if "answer" in item:
                answer = item["answer"]
                if not answer or not str(answer).strip():
                    errors.append(f"Item {idx}: answer is empty or whitespace only")

        if invalid_inventory_ids:
            errors.append(f"Invalid inventory_ids (not in gaps): {invalid_inventory_ids}")

        if duplicate_q_ids:
            errors.append(f"Duplicate q_ids within patch: {duplicate_q_ids}")

        if conflicting_q_ids:
            errors.append(f"q_ids already in forge batch: {conflicting_q_ids}")

        return ValidationResult(
            passed=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )
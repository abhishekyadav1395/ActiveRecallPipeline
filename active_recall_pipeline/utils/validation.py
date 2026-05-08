from __future__ import annotations

import json
import re
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

    def validate_survey(self, output: str, context: dict) -> ValidationResult:
        """Validate SURVEY output: raw text string with numbered concept list."""
        errors = []
        warnings = []

        if not isinstance(output, str):
            return ValidationResult(passed=False, errors=["Output is not a string"])

        if not output or not output.strip():
            return ValidationResult(passed=False, errors=["Output is empty"])

        lines = output.split("\n")
        numbered_lines = [line for line in lines if re.match(r"^\d+\.", line)]

        if len(numbered_lines) < 10:
            errors.append(f"Only {len(numbered_lines)} numbered lines found, minimum is 10")

        long_lines = [
            (i, len(line))
            for i, line in enumerate(lines)
            if len(line) > 300
        ]
        if long_lines:
            for idx, length in long_lines[:5]:
                errors.append(f"Line {idx}: {length} characters, maximum is 300")

        markdown_headers = [i for i, line in enumerate(lines) if re.match(r"^#+\s", line)]
        if markdown_headers:
            errors.append(f"Found {len(markdown_headers)} markdown headers, none allowed")

        chapter_title = context.get("chapter_title", "")
        if chapter_title and chapter_title in output:
            errors.append(f"Output contains chapter title verbatim: '{chapter_title}'")

        return ValidationResult(
            passed=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def validate_consolidate(self, output: list, context: dict) -> ValidationResult:
        """Validate CONSOLIDATE output: structured concept inventory."""
        errors = []
        warnings = []

        if not isinstance(output, list):
            return ValidationResult(passed=False, errors=["Output is not a list"])

        if not output:
            return ValidationResult(passed=False, errors=["Output list is empty"])

        required_keys = {"id", "text", "type", "children"}
        valid_types = {"STANDALONE", "CLUSTER"}
        seen_ids = set()

        for idx, item in enumerate(output):
            item_errors = self._check_required_keys(item, required_keys, idx)
            errors.extend(item_errors)

            if not isinstance(item, dict):
                continue

            if "type" in item and item["type"] not in valid_types:
                errors.append(f"Item {idx}: type='{item['type']}' must be STANDALONE or CLUSTER")

            if "id" in item:
                if not isinstance(item["id"], int):
                    errors.append(f"Item {idx}: id is not an integer (got {type(item['id']).__name__})")
                else:
                    if item["id"] in seen_ids:
                        errors.append(f"Item {idx}: duplicate id {item['id']}")
                    seen_ids.add(item["id"])

            if "text" in item:
                if not item["text"] or not str(item["text"]).strip():
                    errors.append(f"Item {idx}: text is empty or whitespace only")

            if "type" in item and "children" in item:
                children = item["children"]
                if not isinstance(children, list):
                    errors.append(f"Item {idx}: children is not a list")
                elif item["type"] == "STANDALONE":
                    if children:
                        errors.append(f"Item {idx}: STANDALONE type must have empty children list")
                elif item["type"] == "CLUSTER":
                    if len(children) < 3:
                        errors.append(
                            f"Item {idx}: type='CLUSTER' has {len(children)} children, minimum is 3"
                        )

        if seen_ids and max(seen_ids) != len(seen_ids):
            warnings.append(f"Ids not sequential: max id is {max(seen_ids)}, but only {len(seen_ids)} items")

        return ValidationResult(
            passed=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def validate_tier(self, output: list, context: dict) -> ValidationResult:
        """Validate TIER output: tiered concept inventory."""
        errors = []
        warnings = []

        if not isinstance(output, list):
            return ValidationResult(passed=False, errors=["Output is not a list"])

        if not output:
            return ValidationResult(passed=False, errors=["Output list is empty"])

        consolidate_count = context.get("consolidate_count", 0)
        consolidate_ids = set(context.get("consolidate_ids", []))
        valid_tiers = {"SIMPLE", "MEDIUM", "COMPLEX"}
        seen_ids = set()

        for idx, item in enumerate(output):
            item_errors = self._check_required_keys(item, {"id", "tier"}, idx)
            errors.extend(item_errors)

            if not isinstance(item, dict):
                continue

            if "tier" in item and item["tier"] not in valid_tiers:
                errors.append(f"Item {idx}: tier='{item['tier']}' must be SIMPLE, MEDIUM, or COMPLEX")

            if "id" in item:
                if isinstance(item["id"], int):
                    seen_ids.add(item["id"])

        if len(output) != consolidate_count:
            errors.append(f"Count mismatch: tier has {len(output)} items, consolidate has {consolidate_count}")

        missing_ids = consolidate_ids - seen_ids
        if missing_ids:
            sorted_missing = sorted(missing_ids)
            errors.append(f"Missing ids from consolidate: {sorted_missing}")

        return ValidationResult(
            passed=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def validate_excavate(self, output: list, context: dict) -> ValidationResult:
        """Validate EXCAVATE output: prerequisite chains."""
        errors = []
        warnings = []

        if not isinstance(output, list):
            return ValidationResult(passed=False, errors=["Output is not a list"])

        if not output:
            return ValidationResult(passed=False, errors=["Output list is empty"])

        non_simple_ids = set(context.get("non_simple_ids", []))
        required_keys = {"concept_id", "concept_text", "prerequisites"}
        seen_concept_ids = set()

        for idx, item in enumerate(output):
            item_errors = self._check_required_keys(item, required_keys, idx)
            errors.extend(item_errors)

            if not isinstance(item, dict):
                continue

            if "concept_id" in item:
                if isinstance(item["concept_id"], int):
                    seen_concept_ids.add(item["concept_id"])

            if "prerequisites" in item:
                prereqs = item["prerequisites"]
                if not isinstance(prereqs, list):
                    errors.append(f"Item {idx}: prerequisites is not a list")
                    continue

                for p_idx, prereq in enumerate(prereqs):
                    if not isinstance(prereq, dict):
                        errors.append(f"Item {idx}: prerequisite {p_idx} is not a dictionary")
                        continue

                    p_errors = self._check_required_keys(
                        prereq, {"depth", "text", "reason"}, p_idx
                    )
                    for err_msg in p_errors:
                        errors.append(f"Item {idx}: {err_msg}")

                    if "depth" in prereq:
                        depth = prereq["depth"]
                        if not isinstance(depth, int) or depth < 1:
                            errors.append(
                                f"Item {idx}: prerequisite {p_idx} has invalid depth (got {depth}, need >= 1)"
                            )

                if len(prereqs) > 1:
                    depths = []
                    for p in prereqs:
                        if isinstance(p, dict) and "depth" in p and isinstance(p["depth"], int):
                            depths.append(p["depth"])

                    if depths and depths != sorted(depths, reverse=True):
                        warnings.append(
                            f"Item {idx}: prerequisites not ordered by depth descending"
                        )

        missing_ids = non_simple_ids - seen_concept_ids
        if missing_ids:
            sorted_missing = sorted(missing_ids)
            errors.append(f"Missing concept ids: {sorted_missing}")

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
            "Ordering", "Matrix", "Lineage"
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
            "Ordering", "Matrix", "Lineage"
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
                if "GapFill::true" not in tags:
                    errors.append(f"Item {idx}: tags missing 'GapFill::true'")
                if "Inventory::" not in tags:
                    errors.append(f"Item {idx}: tags missing 'Inventory::'")

            if "inventory_id" in item:
                inv_id = item["inventory_id"]
                if inv_id not in gap_ids:
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

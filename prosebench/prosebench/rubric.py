from __future__ import annotations

from importlib import resources
from typing import Any

import yaml
from pydantic import BaseModel, Field, model_validator


class CriterionSpec(BaseModel):
    criterion_id: str
    label: str
    question: str
    anchors: dict[str, str]
    weight: float = Field(gt=0)


class RubricProfile(BaseModel):
    name: str
    label: str
    description: str
    version: str
    criteria: list[CriterionSpec]

    @model_validator(mode="after")
    def validate_profile(self) -> "RubricProfile":
        ids = [item.criterion_id for item in self.criteria]
        if len(ids) != len(set(ids)):
            raise ValueError("Criterion IDs must be unique.")
        total = sum(item.weight for item in self.criteria)
        if round(total, 6) != 100:
            raise ValueError(f"Rubric weights must total 100; found {total}.")
        return self


class RubricLoader:
    package = "prosebench.rubric_data"

    def available_profiles(self) -> list[str]:
        root = resources.files(self.package)
        return sorted(
            item.name.removesuffix(".yaml")
            for item in root.iterdir()
            if item.name.endswith(".yaml") and item.name != "core.yaml"
        )

    def load(self, profile_name: str) -> RubricProfile:
        core = self._read("core.yaml")
        profile = self._read(f"{profile_name}.yaml")
        definitions: list[dict[str, Any]] = core["criteria"]
        weights: dict[str, float] = profile["weights"]
        ids = [item["id"] for item in definitions]
        if set(ids) != set(weights):
            missing = sorted(set(ids) - set(weights))
            extra = sorted(set(weights) - set(ids))
            raise ValueError(f"Profile criterion mismatch. Missing={missing}; extra={extra}")
        criteria = [
            CriterionSpec(
                criterion_id=item["id"],
                label=item["label"],
                question=item["question"],
                anchors={str(key): value for key, value in item["anchors"].items()},
                weight=float(weights[item["id"]]),
            )
            for item in definitions
        ]
        return RubricProfile(
            name=profile_name,
            label=profile["label"],
            description=profile["description"],
            version=str(profile["version"]),
            criteria=criteria,
        )

    def _read(self, filename: str) -> dict[str, Any]:
        target = resources.files(self.package).joinpath(filename)
        if not target.is_file():
            choices = ", ".join(self.available_profiles())
            raise ValueError(f"Unknown profile '{filename.removesuffix('.yaml')}'. Available: {choices}")
        with target.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
        if not isinstance(data, dict):
            raise ValueError(f"Rubric file {filename} must contain a YAML mapping.")
        return data

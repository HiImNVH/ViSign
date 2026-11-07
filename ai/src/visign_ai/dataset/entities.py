"""T009: validated metadata entities; no inferred label or rights approval."""

import re
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum


class Category(StrEnum):
    BASIC = "basic"
    MEDICAL = "medical"
    ADMINISTRATIVE = "administrative"


class Priority(StrEnum):
    P0 = "P0"
    P1 = "P1"


class Region(StrEnum):
    HCM = "HCM"
    HN = "HN"
    HP = "HP"
    OTHER = "OTHER"
    UNKNOWN = "UNKNOWN"


class LicenseStatus(StrEnum):
    APPROVED = "approved"
    RESTRICTED = "restricted"
    UNKNOWN = "unknown"


class VerificationStatus(StrEnum):
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    REJECTED = "rejected"


class DataSplit(StrEnum):
    TRAIN = "train"
    VALIDATION = "validation"
    TEST = "test"


class EntityValidationError(ValueError):
    """Invalid metadata or catalog relationship."""


def text(name: str, value: str) -> None:
    if (not isinstance(value, str) or not value or value != value.strip()
            or unicodedata.normalize("NFC", value) != value
            or any(ord(c) < 32 or ord(c) == 127 for c in value)):
        raise EntityValidationError(f"{name} must be non-empty, trimmed NFC text")


def meaning_id(value: str) -> None:
    text("meaningId", value)
    if not re.fullmatch(r"[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)*", value):
        raise EntityValidationError("meaningId must be UPPER_SNAKE_CASE")


@dataclass(frozen=True, slots=True)
class Meaning:
    meaning_id: str
    display_text: str
    category: Category
    priority: Priority = Priority.P0
    active: bool = True

    def __post_init__(self) -> None:
        meaning_id(self.meaning_id)
        text("displayText", self.display_text)
        try:
            object.__setattr__(self, "category", Category(self.category))
            object.__setattr__(self, "priority", Priority(self.priority))
        except (ValueError, TypeError) as exc:
            raise EntityValidationError("invalid category or priority") from exc
        if type(self.active) is not bool:
            raise EntityValidationError("active must be a boolean")


@dataclass(frozen=True, slots=True)
class SignClass:
    class_label: str
    meaning_id: str
    region: Region
    variant_name: str
    verified: bool = False
    active: bool = False

    def __post_init__(self) -> None:
        meaning_id(self.meaning_id)
        text("classLabel", self.class_label)
        text("variantName", self.variant_name)
        try:
            object.__setattr__(self, "region", Region(self.region))
        except (TypeError, ValueError) as exc:
            raise EntityValidationError("invalid region") from exc
        if not re.fullmatch(r"[1-9][0-9]*", self.variant_name):
            raise EntityValidationError("variantName must be a positive integer without zero padding")
        if self.class_label != f"{self.meaning_id}_{self.region}_{self.variant_name}":
            raise EntityValidationError("classLabel must match meaningId/region/variantName")
        if type(self.verified) is not bool or type(self.active) is not bool:
            raise EntityValidationError("verified and active must be booleans")


def validate_catalog(
    meanings: Iterable[Meaning], classes: Iterable[SignClass],
) -> tuple[dict[str, Meaning], dict[str, SignClass]]:
    """Enforce unique IDs/variant identities and class-to-meaning references."""
    by_meaning: dict[str, Meaning] = {}
    by_class: dict[str, SignClass] = {}
    variants: set[tuple[str, Region, str]] = set()
    for meaning in meanings:
        if meaning.meaning_id in by_meaning:
            raise EntityValidationError("duplicate meaningId")
        by_meaning[meaning.meaning_id] = meaning
    for sign_class in classes:
        if sign_class.meaning_id not in by_meaning:
            raise EntityValidationError("SignClass references missing Meaning")
        identity = (sign_class.meaning_id, sign_class.region, sign_class.variant_name)
        if sign_class.class_label in by_class or identity in variants:
            raise EntityValidationError("duplicate classLabel or meaning/region/variant")
        if sign_class.active and not by_meaning[sign_class.meaning_id].active:
            raise EntityValidationError("active SignClass requires an active Meaning")
        by_class[sign_class.class_label] = sign_class
        variants.add(identity)
    return by_meaning, by_class

# tests/contract/test_api_contract_drift.py
# Drift test T099: openapi.yaml, Python domain va TypeScript types phai khop enum, field, required va nullable.
import re
from pathlib import Path
from typing import Any, NamedTuple, get_args

import pytest
import yaml
from pydantic import BaseModel
from visign_api.domain.errors import ErrorCode, ErrorEnvelope
from visign_api.domain.health import HealthResponse, HealthStatus
from visign_api.domain.model_version import ArtifactKind, ModelInfoResponse
from visign_api.domain.prediction import (
    OPTIONAL_DIAGNOSTIC_FIELDS,
    PredictionQualityHints,
    PredictionResponse,
    PredictionTimings,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
OPENAPI_PATH = (
    REPOSITORY_ROOT / "specs" / "001-vsl-recognition-mvp" / "contracts" / "openapi.yaml"
)
TYPESCRIPT_TYPES_PATH = (
    REPOSITORY_ROOT / "apps" / "web" / "src" / "types" / "inference-api.ts"
)

# D1 trong docs/contracts/api-conventions.md
AGREED_422_DESCRIPTION = (
    "Clip cannot be decoded or does not satisfy inference constraints"
)

PYTHON_MODEL_BY_SCHEMA: dict[str, type[BaseModel]] = {
    "HealthResponse": HealthResponse,
    "ModelInfo": ModelInfoResponse,
    "PredictionResponse": PredictionResponse,
    "PredictionTimings": PredictionTimings,
    "PredictionQualityHints": PredictionQualityHints,
    "ErrorEnvelope": ErrorEnvelope,
}
TYPESCRIPT_SCHEMAS = list(PYTHON_MODEL_BY_SCHEMA)
# Field optional bi bo khoi JSON khi vang (khong bao gio null); field optional khac co the null
OMITTED_WHEN_ABSENT_BY_SCHEMA: dict[str, frozenset[str]] = {
    "PredictionResponse": frozenset(OPTIONAL_DIAGNOSTIC_FIELDS),
}

INTERFACE_PATTERN = re.compile(r"export interface (\w+) \{\n(.*?)\n\}", re.DOTALL)
FIELD_PATTERN = re.compile(r"^\s+(\w+)(\??): (.+);$", re.MULTILINE)
CONST_ARRAY_PATTERN = r"export const {name} = \[(.*?)\] as const;"


class FieldShape(NamedTuple):
    required: frozenset[str]
    nullable: frozenset[str]
    names: frozenset[str]


@pytest.fixture(scope="module")
def openapi_schemas() -> dict[str, Any]:
    openapi_contract: dict[str, Any] = yaml.safe_load(
        OPENAPI_PATH.read_text(encoding="utf-8")
    )
    component_schemas: dict[str, Any] = openapi_contract["components"]["schemas"]
    return component_schemas


@pytest.fixture(scope="module")
def typescript_source() -> str:
    return TYPESCRIPT_TYPES_PATH.read_text(encoding="utf-8")


def openapi_shape(schema: dict[str, Any]) -> FieldShape:
    properties: dict[str, Any] = schema["properties"]
    nullable_names = {
        property_name
        for property_name, property_schema in properties.items()
        if isinstance(property_schema.get("type"), list)
        and "null" in property_schema["type"]
    }
    return FieldShape(
        frozenset(schema.get("required", [])),
        frozenset(nullable_names),
        frozenset(properties),
    )


def python_shape(
    model: type[BaseModel], omitted_when_absent: frozenset[str]
) -> FieldShape:
    required_names = {
        name for name, field in model.model_fields.items() if field.is_required()
    }
    # Kieu co None la nullable, tru field optional bi bo khoi JSON khi vang (timingsMs, qualityHints)
    nullable_names = {
        name
        for name, field in model.model_fields.items()
        if type(None) in get_args(field.annotation) and name not in omitted_when_absent
    }
    return FieldShape(
        frozenset(required_names),
        frozenset(nullable_names),
        frozenset(model.model_fields),
    )


def typescript_shape(typescript_source: str, interface_name: str) -> FieldShape:
    interfaces = {
        name: body for name, body in INTERFACE_PATTERN.findall(typescript_source)
    }
    assert interface_name in interfaces, (
        f"Thieu interface {interface_name} trong inference-api.ts"
    )
    fields = FIELD_PATTERN.findall(interfaces[interface_name])
    required_names = {
        name for name, optional_marker, _ in fields if not optional_marker
    }
    nullable_names = {
        name for name, optional_marker, field_type in fields if "| null" in field_type
    }
    return FieldShape(
        frozenset(required_names),
        frozenset(nullable_names),
        frozenset(name for name, _, _ in fields),
    )


def typescript_const_values(typescript_source: str, const_name: str) -> list[str]:
    match = re.search(
        CONST_ARRAY_PATTERN.format(name=const_name), typescript_source, re.DOTALL
    )
    assert match is not None, f"Thieu hang so {const_name} trong inference-api.ts"
    return re.findall(r"'([^']+)'", match.group(1))


def test_error_codes_match_across_openapi_python_and_typescript(
    openapi_schemas: dict[str, Any], typescript_source: str
) -> None:
    # D3: moi ma loi trong OpenAPI phai co trong TS truoc khi backend phat hanh
    contract_codes = openapi_schemas["ErrorEnvelope"]["properties"]["code"]["enum"]

    assert [error_code.value for error_code in ErrorCode] == contract_codes
    assert typescript_const_values(typescript_source, "ERROR_CODES") == contract_codes


def test_artifact_kinds_match_across_openapi_python_and_typescript(
    openapi_schemas: dict[str, Any], typescript_source: str
) -> None:
    contract_kinds = openapi_schemas["ModelInfo"]["properties"]["artifactKind"]["enum"]

    assert [artifact_kind.value for artifact_kind in ArtifactKind] == contract_kinds
    assert (
        typescript_const_values(typescript_source, "ARTIFACT_KINDS") == contract_kinds
    )


def test_health_statuses_match_between_openapi_and_typescript(
    openapi_schemas: dict[str, Any], typescript_source: str
) -> None:
    contract_statuses = openapi_schemas["HealthResponse"]["properties"]["status"][
        "enum"
    ]

    assert (
        typescript_const_values(typescript_source, "HEALTH_STATUSES")
        == contract_statuses
    )
    assert list(get_args(HealthStatus)) == contract_statuses


@pytest.mark.parametrize("schema_name", list(PYTHON_MODEL_BY_SCHEMA))
def test_python_models_match_openapi_fields(
    schema_name: str, openapi_schemas: dict[str, Any]
) -> None:
    omitted_when_absent = OMITTED_WHEN_ABSENT_BY_SCHEMA.get(schema_name, frozenset())

    assert python_shape(
        PYTHON_MODEL_BY_SCHEMA[schema_name], omitted_when_absent
    ) == openapi_shape(openapi_schemas[schema_name])


@pytest.mark.parametrize("schema_name", TYPESCRIPT_SCHEMAS)
def test_typescript_interfaces_match_openapi_fields(
    schema_name: str, openapi_schemas: dict[str, Any], typescript_source: str
) -> None:
    assert typescript_shape(typescript_source, schema_name) == openapi_shape(
        openapi_schemas[schema_name]
    )


def test_unprocessable_clip_description_follows_decision_d1() -> None:
    openapi_contract: dict[str, Any] = yaml.safe_load(
        OPENAPI_PATH.read_text(encoding="utf-8")
    )
    unprocessable_response = openapi_contract["paths"]["/api/v1/predictions"]["post"][
        "responses"
    ]["422"]

    assert unprocessable_response["description"] == AGREED_422_DESCRIPTION

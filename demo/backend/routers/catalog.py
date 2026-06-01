"""Catalog endpoint: expose the Layer B schema catalog for the frontend.

Application-layer metadata only — the codec catalog (baseball_ticket /
festival_pass / wristband) is demo policy, not part of the patent claim.
"""
from __future__ import annotations

from fastapi import APIRouter

from ..layer_b_codec import SCHEMA_CATALOG
from ..schemas import SchemaFieldInfo, SchemaInfo, SchemaListResponse

router = APIRouter(prefix="/api", tags=["catalog"])


@router.get("/schemas", response_model=SchemaListResponse)
def list_schemas() -> SchemaListResponse:
    """List each Layer B schema with its field descriptors.

    `required` is derived from the pydantic model field; `is_timestamp` from the
    schema's aggressive-form timestamp fields. `kind` is omitted from the field
    list (it's the discriminator, fixed per schema).
    """
    schemas: list[SchemaInfo] = []
    for schema in SCHEMA_CATALOG.values():
        fields: list[SchemaFieldInfo] = []
        for name, field in schema.model.model_fields.items():
            if name == "kind":
                continue
            fields.append(
                SchemaFieldInfo(
                    name=name,
                    required=field.is_required(),
                    is_timestamp=name in schema.ts_fields,
                )
            )
        schemas.append(
            SchemaInfo(kind=schema.kind, schema_id=schema.schema_id, fields=fields)
        )
    return SchemaListResponse(schemas=schemas)

from collections import defaultdict
from enum import Enum
from typing import Union

from fastapi import Depends, FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator
from sqlmodel import Session

from microservice.db.engine import create_tables, get_session
from microservice.db.models import Component, Workflow

app = FastAPI()


@app.on_event("startup")
def start_db():
    create_tables()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    reformatted_error_messages = defaultdict(list)
    for validations_errors in exc.errors():
        error_message = validations_errors.get("msg", "")
        invalid_field_raw = validations_errors.get("loc", "")

        invalid_field = (
            invalid_field_raw[1:]
            if invalid_field_raw[0] in ("body", "query", "path")
            else invalid_field_raw
        )
        invalid_field_path = ".".join([str(x) for x in invalid_field])

        reformatted_error_messages[invalid_field_path].append(error_message)

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder(
            {"detail": "Invalid request", "errors": reformatted_error_messages}
        ),
    )


class ComponentTypeEnum(str, Enum):
    IMPORT = "import"
    SHADOW = "shadow"
    CROP = "crop"
    EXPORT = "export"


class ComponentSchema(BaseModel):
    type: ComponentTypeEnum
    settings: dict[str, Union[int, float, str, bool]] | None = None


class WorkflowSchema(BaseModel):
    name: str
    components: list[ComponentSchema] = []

    @field_validator("components")
    def validate_components_uniqueness(cls, components):
        unique_components_types = set()
        duplicated_components_types = set()

        for c in components:
            if c.type in unique_components_types:
                duplicated_components_types.add(c.type)
            unique_components_types.add(c.type)

        if duplicated_components_types:
            duplicated_components_types_str = ", ".join(
                [c.value for c in duplicated_components_types]
            )
            raise ValueError(f"Duplicated types: {duplicated_components_types_str}")

        return components

    @field_validator("components")
    def validate_components_import_export_position(cls, components):
        import_index = next(
            (i for i, c in enumerate(components) if c.type == ComponentTypeEnum.IMPORT),
            None,
        )
        export_index = next(
            (i for i, c in enumerate(components) if c.type == ComponentTypeEnum.EXPORT),
            None,
        )

        # neither import nor export components are present
        if import_index is None and export_index is None:
            return components

        if export_index is not None and export_index != len(components) - 1:
            if import_index is not None and import_index != 0:
                raise ValueError(
                    "'import' must be at the start and 'export' must be at the end of components"
                )
            raise ValueError("'export' must be at the end of components")

        if import_index is not None and import_index != 0:
            raise ValueError("'import' must be at the start of components")

        return components

    @field_validator("components")
    def validate_components_settings(cls, components):
        has_settings = [c.settings is not None for c in components]

        if any(has_settings) and not all(has_settings):
            raise ValueError(
                "settings must either be present or missing for all components"
            )

        return components


@app.post("/workflow")
def create_workflow(request: WorkflowSchema, session: Session = Depends(get_session)):
    components_db = [
        Component(
            type=c.type.value,
            settings=c.settings,
        )
        for c in request.components
    ]
    workflow_db = Workflow(
        name=request.name,
        components=components_db,
    )
    session.add(workflow_db)
    session.commit()
    session.refresh(workflow_db)
    return JSONResponse(content={"workflow_id": str(workflow_db.id)})

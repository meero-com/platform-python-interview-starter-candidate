from pydantic import BaseModel
from pydantic.functional_validators import field_validator
from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import Session
from typing import Union
from microservice.db.engine import create_tables, get_session
from microservice.db.models import Workflow
from .db.models import WorkflowComponentType, WorkflowComponentModel

app = FastAPI()


@app.on_event("startup")
def start_db():
    create_tables()


# TODO: add list of components with `type` and `settings` fields to the request


class WorkflowComponentSchema(BaseModel):
    type: WorkflowComponentType
    settings: dict[str, Union[int, float, str, bool]] | None = None


class WorkflowSchema(BaseModel):
    name: str
    components: list[WorkflowComponentSchema] | None = None

    @field_validator("components")
    @classmethod
    def validate_unique_component_types(cls, components):
        components_types = [item.type for item in components]
        if len(components_types) != len(set(components_types)):
            raise ValueError("Component types must be unique")
        return components

    @field_validator("components")
    @classmethod
    def validate_positions_of_import_and_export_component_types(cls, components):
        component_types_dict = {
            item.type: index for index, item in enumerate(components)
        }
        if (WorkflowComponentType.IMPORT in component_types_dict) and (
            component_types_dict[WorkflowComponentType.IMPORT] != 0
        ):
            raise ValueError("Import component is not the first in the list")
        if (WorkflowComponentType.EXPORT in component_types_dict) and (
            component_types_dict[WorkflowComponentType.EXPORT] != len(components) - 1
        ):
            raise ValueError("Export component is not the last in the list")
        return components

    @field_validator("components")
    @classmethod
    def validate_component_sttings_either_all_contain_or_all_not_contain(
        cls, components
    ):
        if not (
            all(item.settings is None for item in components)
            or all(item.settings is not None for item in components)
        ):
            raise ValueError(
                "Either all components should contain settings or all should not"
            )
        return components


@app.post("/workflow")
def create_workflow(request: WorkflowSchema, session: Session = Depends(get_session)):
    # TODO: validate and store components
    try:
        workflow_db = Workflow(name=request.name)
        session.add(workflow_db)
        session.commit()
        session.refresh(workflow_db)

        if request.components:
            for component in request.components:
                component_db = WorkflowComponentModel(
                    workflow_id=str(workflow_db.id),
                    type=component.type,
                )
                component_db.settings = component.settings
                session.add(component_db)
            session.commit()

        return workflow_db.id
    except ValueError as a:
        raise HTTPException(status_code=400, detail=str(a))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

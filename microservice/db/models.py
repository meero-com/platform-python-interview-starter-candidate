import json
from uuid import uuid4, UUID
from sqlmodel import Field, SQLModel, Relationship
from typing import Union, Optional, List
from enum import Enum


class WorkflowComponentType(str, Enum):
    IMPORT = "import"
    SHADOW = "shadow"
    CROP = "crop"
    EXPORT = "export"


class Workflow(SQLModel, table=True):
    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )
    name: str
    components: List["WorkflowComponentModel"] = Relationship(back_populates="workflow")


# TODO: add tables for `WorkflowComponentModel` and `WorkflowSettingsModel`
class WorkflowComponentModel(SQLModel, table=True):
    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )
    type: WorkflowComponentType

    workflow_id: Optional[int] = Field(default=None, foreign_key="workflow.id")
    workflow: Optional["Workflow"] = Relationship(back_populates="components")

    settings_json_str: Optional[str] = Field(default=None, alias="settings")

    @property
    def settings(self):
        return json.loads(self.settings_json_str) if self.settings_json_str else None

    @settings.setter
    def settings(self, settings_dict: dict):
        self.settings_json_str = json.dumps(settings_dict) if settings_dict else None

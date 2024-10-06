from enum import Enum
from typing import Dict, Optional
from uuid import UUID, uuid4

from sqlalchemy.types import JSON
from sqlmodel import Column, Field, Relationship, SQLModel


class ComponentTypeEnum(str, Enum):
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
    components: list["Component"] = Relationship(back_populates="workflow")


class Component(SQLModel, table=True):
    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )
    type: ComponentTypeEnum = Field()
    settings: Dict = Field(default_factory=None, sa_column=Column(JSON))
    workflow_id: Optional[UUID] = Field(default=None, foreign_key="workflow.id")
    workflow: Optional[Workflow] = Relationship(back_populates="components")

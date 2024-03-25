from unittest import TestCase
from assertpy import assert_that
from fastapi.testclient import TestClient
from microservice.db.engine import get_test_session, get_session

from microservice.api import app
from microservice.db.models import (
    Workflow,
    WorkflowComponentModel,
    WorkflowComponentType,
)


class TestAPI(TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        app.dependency_overrides[get_session] = get_test_session
        cls.client = TestClient(app)

    @classmethod
    def tearDown(cls) -> None:
        app.dependency_overrides.clear()

    def test_should_create_workflow_with_name(self):
        given_workflow = {"name": "test"}

        response = self.client.post("/workflow/", json=given_workflow)

        assert_that(response.status_code).is_equal_to(200)
        workflow_id = response.json()
        assert_that(workflow_id).is_instance_of(str)

        # without a GET endpoint, we look directly in the db
        with next(get_test_session()) as session:
            wf = session.get(Workflow, workflow_id)
            assert_that(str(wf.id)).is_equal_to(workflow_id)
            assert_that(wf.name).is_equal_to(given_workflow["name"])

    # TODO: test components support and validation

    def test_should_not_allow_duplicate_component_types_success(self):
        given_workflow = {
            "name": "test",
            "components": [
                {"type": WorkflowComponentType.IMPORT, "settings": None},
                {"type": WorkflowComponentType.CROP, "settings": None},
            ],
        }

        response = self.client.post("/workflow/", json=given_workflow)

        assert_that(response.status_code).is_equal_to(200)
        workflow_id = response.json()
        assert_that(workflow_id).is_instance_of(str)

        with next(get_test_session()) as session:
            wf = session.get(Workflow, workflow_id)
            assert_that(str(wf.id)).is_equal_to(workflow_id)
            assert_that(wf.name).is_equal_to(given_workflow["name"])

    def test_should_not_allow_duplicate_component_types_error(self):
        given_workflow = {
            "name": "test",
            "components": [
                {"type": WorkflowComponentType.IMPORT, "settings": None},
                {"type": WorkflowComponentType.IMPORT, "settings": None},
            ],
        }

        response = self.client.post("/workflow/", json=given_workflow)

        assert_that(response.status_code).is_equal_to(422)
        error_messages = ", ".join(
            [error["msg"] for error in response.json()["detail"]]
        )
        assert_that(error_messages).contains("Component types must be unique")

    def test_should_validate_import_and_export_positions_success(self):
        given_workflow = {
            "name": "test",
            "components": [
                {"type": WorkflowComponentType.CROP, "settings": None},
                {"type": WorkflowComponentType.EXPORT, "settings": None},
            ],
        }

        response = self.client.post("/workflow/", json=given_workflow)

        assert_that(response.status_code).is_equal_to(200)
        workflow_id = response.json()
        assert_that(workflow_id).is_instance_of(str)

        with next(get_test_session()) as session:
            wf = session.get(Workflow, workflow_id)
            assert_that(str(wf.id)).is_equal_to(workflow_id)
            assert_that(wf.name).is_equal_to(given_workflow["name"])

            wfc = session.query(WorkflowComponentModel).all()
            print("wfc", len(wfc))

    def test_should_validate_import_and_export_positions_error(self):
        given_workflow = {
            "name": "test",
            "components": [
                {"type": WorkflowComponentType.CROP, "settings": None},
                {"type": WorkflowComponentType.IMPORT, "settings": None},
            ],
        }

        response = self.client.post("/workflow/", json=given_workflow)

        assert_that(response.status_code).is_equal_to(422)
        error_messages = ", ".join(
            [error["msg"] for error in response.json()["detail"]]
        )
        assert_that(error_messages).contains(
            "Import component is not the first in the list"
        )

    def test_should_validate_settings_consistency_success(self):
        given_workflow = {
            "name": "test",
            "components": [
                {"type": WorkflowComponentType.SHADOW, "settings": {"param": "value"}},
                {"type": WorkflowComponentType.CROP, "settings": {"param": "value"}},
            ],
        }

        response = self.client.post("/workflow/", json=given_workflow)
        # print("response", response)
        # print("response.status_code", response.status_code)
        # print("response json", response.json())

        assert_that(response.status_code).is_equal_to(200)
        workflow_id = response.json()
        assert_that(workflow_id).is_instance_of(str)

        with next(get_test_session()) as session:
            wf = session.get(Workflow, workflow_id)
            assert_that(str(wf.id)).is_equal_to(workflow_id)
            assert_that(wf.name).is_equal_to(given_workflow["name"])

    def test_should_validate_settings_consistency_error(self):
        given_workflow = {
            "name": "test",
            "components": [
                {"type": WorkflowComponentType.SHADOW, "settings": None},
                {"type": WorkflowComponentType.CROP, "settings": {"param": "value"}},
            ],
        }

        response = self.client.post("/workflow/", json=given_workflow)

        assert_that(response.status_code).is_equal_to(422)
        error_messages = ", ".join(
            [error["msg"] for error in response.json()["detail"]]
        )
        assert_that(error_messages).contains(
            "Either all components should contain settings or all should not"
        )

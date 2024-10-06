import uuid
from unittest import TestCase

from assertpy import assert_that
from fastapi.testclient import TestClient
from parameterized import parameterized

from microservice.api import app
from microservice.db.engine import get_session, get_test_session
from microservice.db.models import ComponentTypeEnum, Workflow


class TestAPI(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        app.dependency_overrides[get_session] = get_test_session
        cls.client = TestClient(app)

    @classmethod
    def tearDown(cls) -> None:
        app.dependency_overrides.clear()

    def test_workflow_with_invalid_components_type_should_return_422(self):
        payload = {"name": "component_name", "components": [{"type": "zoom"}]}

        response = self.client.post("/workflow/", json=payload)
        errors = response.json()["errors"]

        assert_that(response.status_code).is_equal_to(422)
        assert_that(errors["components.0.type"]).is_equal_to(
            ["Input should be 'import', 'shadow', 'crop' or 'export'"]
        )

    def test_workflow_with_invalid_settings_should_return_422(self):
        payload = {
            "name": "component_name",
            "components": [{"type": "crop", "settings": {"a": {"b": 11}}}],
        }
        response = self.client.post("/workflow/", json=payload)
        errors = response.json()["errors"]

        assert_that(response.status_code).is_equal_to(422)
        assert_that(errors["components.0.settings.a.int"]).is_equal_to(
            ["Input should be a valid integer"]
        )
        assert_that(errors["components.0.settings.a.str"]).is_equal_to(
            ["Input should be a valid string"]
        )
        assert_that(errors["components.0.settings.a.float"]).is_equal_to(
            ["Input should be a valid number"]
        )
        assert_that(errors["components.0.settings.a.bool"]).is_equal_to(
            ["Input should be a valid boolean"]
        )

    def test_workflow_with_duplicated_types_should_return_422(self):
        payload = {
            "name": "component_name",
            "components": [{"type": "crop"}, {"type": "crop"}],
        }

        response = self.client.post("/workflow/", json=payload)
        errors = response.json()["errors"]

        assert_that(response.status_code).is_equal_to(422)
        assert_that(errors["components"]).is_equal_to(
            ["Value error, Duplicated types: crop"]
        )

    @parameterized.expand(
        [
            [
                "import_export_mispositioned",
                {
                    "name": "component_name",
                    "components": [
                        {"type": "crop"},
                        {"type": "import"},
                        {"type": "export"},
                        {"type": "shadow"},
                    ],
                },
                [
                    "Value error, 'import' must be at the start and 'export' must be at the end of components"
                ],
            ],
            [
                "import_not_at_start",
                {
                    "name": "test",
                    "components": [
                        {"type": "shadow"},
                        {"type": "import"},
                    ],
                },
                ["Value error, 'import' must be at the start of components"],
            ],
            [
                "export_not_at_end",
                {
                    "name": "component_name",
                    "components": [
                        {"type": "export"},
                        {"type": "shadow"},
                    ],
                },
                ["Value error, 'export' must be at the end of components"],
            ],
        ]
    )
    def test_workflow_with_invalid_import_export_components_should_return_422(
        self, name, payload, error_message
    ):
        response = self.client.post("/workflow/", json=payload)
        errors = response.json()["errors"]

        assert_that(response.status_code).is_equal_to(422)
        assert_that(errors["components"]).is_equal_to(error_message)

    def test_workflow_with_inconsistent_settings_should_return_422(self):
        payload = {
            "name": "component_name",
            "components": [
                {"type": "crop", "settings": {"key": 11}},
                {"type": "export"},
            ],
        }

        response = self.client.post("/workflow/", json=payload)
        errors = response.json()["errors"]

        assert_that(response.status_code).is_equal_to(422)
        assert_that(errors["components"]).is_equal_to(
            [
                "Value error, settings must either be present or missing for all components"
            ]
        )

    def test_workflow_with_valid_compoenent_payload_should_return_200(self):
        payload = {
            "name": "name",
            "components": [
                {"type": "import"},
                {"type": "crop"},
            ],
        }
        response = self.client.post("/workflow/", json=payload)

        assert_that(response.status_code).is_equal_to(200)

    def test_should_create_workflow_with_name(self):
        given_workflow = {"name": "test"}

        response = self.client.post("/workflow/", json=given_workflow)
        response_body = response.json()

        assert_that(response.status_code).is_equal_to(200)
        assert_that(response_body["workflow_id"]).is_instance_of(str)
        workflow_id = response_body["workflow_id"]

        # without a GET endpoint, we look directly in the db
        with next(get_test_session()) as session:
            wf = session.get(Workflow, uuid.UUID(workflow_id))
            assert_that(str(wf.id)).is_equal_to(workflow_id)
            assert_that(wf.name).is_equal_to(given_workflow["name"])

    def test_should_create_workflow_with_components(self):
        given_workflow = {
            "name": "test",
            "components": [{"type": "crop"}, {"type": "shadow"}],
        }

        response = self.client.post("/workflow/", json=given_workflow)
        response_body = response.json()

        assert_that(response.status_code).is_equal_to(200)
        assert_that(response_body["workflow_id"]).is_instance_of(str)
        workflow_id = response_body["workflow_id"]

        # without a GET endpoint, we look directly in the db
        with next(get_test_session()) as session:
            wf = session.get(Workflow, uuid.UUID(workflow_id))
            assert_that(str(wf.id)).is_equal_to(workflow_id)
            assert_that(len(wf.components)).is_equal_to(2)
            assert_that(wf.components[0].type).is_equal_to(ComponentTypeEnum.CROP)
            assert_that(wf.components[0].settings).is_none()
            assert_that(wf.components[1].type).is_equal_to(ComponentTypeEnum.SHADOW)
            assert_that(wf.components[1].settings).is_none()

    def test_should_create_workflow_with_settings(self):
        settings = {"zoom": 2, "render": False}
        given_workflow = {
            "name": "test",
            "components": [{"type": "crop", "settings": settings}],
        }

        response = self.client.post("/workflow/", json=given_workflow)
        response_body = response.json()

        assert_that(response.status_code).is_equal_to(200)
        assert_that(response_body["workflow_id"]).is_instance_of(str)
        workflow_id = response_body["workflow_id"]

        # without a GET endpoint, we look directly in the db
        with next(get_test_session()) as session:
            wf = session.get(Workflow, uuid.UUID(workflow_id))
            assert_that(str(wf.id)).is_equal_to(workflow_id)
            assert_that(len(wf.components)).is_equal_to(1)
            assert_that(wf.components[0].type).is_equal_to(ComponentTypeEnum.CROP)
            assert_that(wf.components[0].settings).is_equal_to(settings)

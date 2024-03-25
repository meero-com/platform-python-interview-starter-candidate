# Python interview starter

## Task description

- Tech: fatapi, sqlmodel
- Function: POST `/workflow/` allower user to create new workflows.

### TODO

- Input: an optional list of components, one component data structure

```python
from enum import Enum

class WorkflowComponentType(str, Enum):
  IMPORT = "import"
  SHADOW = "sahdow"
  CROP = "crop"
  EXPORT = "export"

class WorkflowComponent(BaseModel):
  type: WorkflowComponentType
  settings: dict[str, [int | float | str | bool]] | None = None

class WorkflowSchema(BaseModel):
  name: str
  components: list[WorkflowComponent]

```

## Setup

we recommend you create some virtual environment with a python version >= 3.11, e.g.

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt && pip install -r requirements.test.txt
```

run the tests with

```bash
python -m unittest discover
```

## Instructions

### Context

This repo contains a simple HTTP microservice, with a single endpoint, `POST /workflow/`, to allow clients to create new workflows.
It is implemented with `fastapi` and `sqlmodel` (running a simple `sqlite` db).
For now, `POST /workflow/` accepts a JSON with only one property `name: str`.

### TODO

Your task is

- [ ] to extend the `/workflow/` endpoint to also accept an optional list of components in its request and store it in the database
  - a component is a dictionary containing two fields
    - `type` (required) whose value must be one of `{"import", "shadow", "crop", "export"}`
    - and `settings` (optional), a dictionary mapping strings (name of the setting) to a value whose type must be one of `{int, float, str, bool}`

> an example of request could then be
>
> ```
> {
>  "name": "MyWorkflow",
>  "components": [
>    {"type": "import", "settings": {"format": "PNG", "downscale":  true}},
>    {"type": "shadow", "settings": {"intensity": 0.1}}
>  ]
> }
> ```

- [ ] the list of components must be validated according to the following rules:
  - [ ] the list should not contain two components of the same `type`
  - [ ] if present, component of `type` `"import"` and `"export"` must be, respectively, first and last in the list
  - [ ] all components should either all contain the `settings` field or none shall contain it.
- [ ] if the input validation fails, the endpoint should return an appropriate status code and a helpful message
- [ ] provide tests to show
  - [ ] that the endpoint now supports the new JSON schema
  - [ ] and enforces the rules for the input validation

You can base your tests on `tests/test_create_workflow.py` but please, do not modify `test_should_create_workflow_with_name()` since this test still needs to be green once you are done!

> The source code contains comments with `# TODO:` to guide you.

Once you are finished, please

- push this repo to your github with your solution on a feature branch
- make the github repo private
- allow at least one of the following users to read the repo:
  - oliver-autoretouch
  - jfouca

Finally, please feel free to make this repo yours! You're allowed to change anything and everything!

Good luck and have fun!

# Python interview starter

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

# Quality
python -m black .
python -m flake8 .
python -m isort .
```


run the application

```bash
# Optional, delete the database
rm -f microservice.db
# Run the API
python -m fastapi dev microservice/api.py
```

## Instructions

### Context

This repo contains a simple HTTP microservice, with a single endpoint, `POST /workflow/`, to allow clients to create new workflows.
It is implemented with `fastapi` and `sqlmodel` (running a simple `sqlite` db).
For now, `POST /workflow/` accepts a JSON with only one property `name: str`.

### TODO

Your task is
- [x] to extend the `/workflow/` endpoint to also accept an optional list of components in its request and store it in the database
  - a component is a dictionary containing two fields 
    - `type` (required) whose value must be one of `{"import", "shadow", "crop", "export"}`
    - and `settings` (optional), a dictionary mapping strings (name of the setting) to a value whose type must be one of `{int, float, str, bool}`

>  an example of request could then be
> ```
> {
>  "name": "MyWorkflow",
>  "components": [
>    {"type": "import", "settings": {"format": "PNG", "downscale":  true}},
>    {"type": "shadow", "settings": {"intensity": 0.1}}
>  ]
> }

- [x] the list of components must be validated according to the following rules:
  - [x] the list should not contain two components of the same `type`
  - [x] if present, component of `type` `"import"` and `"export"` must be, respectively, first and last in the list
  - [x] all components should either all contain the `settings` field or none shall contain it.
- [x] if the input validation fails, the endpoint should return an appropriate status code and a helpful message
- [x] provide tests to show
  - [x] that the endpoint now supports the new JSON schema
  - [x] and enforces the rules for the input validation

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

# Asumptions / Decisions
- Validation is done at pydantic level as all the validations rules are based on the input.
- Settings storage: one naive approach would be to store each settings in a row in a dedicated Setting table with a foreign key to the related component. If we would go that way, it would require to have a `key`, `value` and `type` columns as we receive a dictionary mapping a name with an heterogeneous value (either a int, float, string or boolean value). The alternative was to store it as JSON as we can easily go back and forth between dict and JSON. So because of that, it's making more sense to have the settings into the `Component` table instead of inside a `Setting` table if stored as JSON (prevent an unnecessary join for a 0,1 relationship).
Storing as JSON instead of rows in a `Setting` also help reducing the number of necessary joins to retrive the workflow, ease the reconstruction of the settings (instead of having to check the `type` and cast it back to the correct type)
- Validation error handling: the response returned by default by FastAPI is complete but a little too complicated with a lot of information. I have set up a handler in order to simply the response


# Improvements
- Better separation of concern: do not call database directly in the controller by using Service Layer or Repository Pattern
- Better error message for `settings` value validation: at the moment, if the setting value is neither an int, float, string or boolean, the validation will fail (as expected) but will trigger 4 errors messages (one for each authorised type). It would be clearer for the end user to have one single error to digest instead of 4
- Store the type as the enum value (lowercased) instead of the Enum name
- Improve the response returned on request validation failing

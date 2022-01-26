from test.utils import load_event


def test_get_device(app):
    mock_event = load_event("graphql/getDevice_cognito.json")

    result = app.graphql.handle(mock_event, {})

    print(result.formatted)

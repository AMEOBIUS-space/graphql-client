import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from client import QueryBuilder, GraphQLVariable, GraphQLFragment, GraphQLClient, GraphQLResponse


def test_query_builder_basic():
    qb = QueryBuilder("query", "GetUser")
    qb.add_field("user", args={"id": "123"}, subfields=["id", "name", "email"])
    query = qb.build()
    assert "query GetUser" in query
    assert "user(id: 123)" in query
    assert "name" in query


def test_query_builder_variables():
    qb = QueryBuilder("query", "GetUser")
    qb.add_variable("id", "ID!", required=True)
    qb.add_field("user", args={"id": "$id"}, subfields=["name"])
    query = qb.build()
    assert "$id: ID!" in query
    assert "user(id: $id)" in query


def test_query_builder_mutation():
    qb = QueryBuilder("mutation", "CreateUser")
    qb.add_variable("input", "CreateUserInput!", required=True)
    qb.add_field("createUser", args={"input": "$input"}, subfields=["id", "name"])
    query = qb.build()
    assert "mutation CreateUser" in query
    assert "createUser(input: $input)" in query


def test_query_builder_nested():
    qb = QueryBuilder("query")
    qb.add_field("user", subfields=[
        "id", "name",
        "posts { id title }",
        "profile { bio avatar }"
    ])
    query = qb.build()
    assert "posts" in query
    assert "profile" in query


def test_query_builder_fragment():
    frag = GraphQLFragment("UserFields", "User", ["id", "name", "email"])
    qb = QueryBuilder("query", "GetUser")
    qb.add_fragment(frag)
    query = qb.build()
    assert "...UserFields" in query
    assert "fragment UserFields on User" in query


def test_variable_declaration():
    v = GraphQLVariable("id", "ID", required=True)
    assert v.declaration() == "$id: ID!"

    v2 = GraphQLVariable("limit", "Int", default="10")
    assert "= 10" in v2.declaration()


def test_fragment_render():
    frag = GraphQLFragment("PostFields", "Post", ["id", "title", "body"])
    rendered = frag.render()
    assert "fragment PostFields on Post" in rendered
    assert "title" in rendered


def test_graphql_response_data():
    resp = GraphQLResponse({"data": {"user": {"name": "Alice"}}})
    assert resp.has_data
    assert not resp.has_errors
    assert resp.get("user.name") == "Alice"


def test_graphql_response_errors():
    resp = GraphQLResponse({"errors": [{"message": "Not found"}]})
    assert resp.has_errors
    assert not resp.has_data
    assert "Not found" in resp.error_messages()


def test_graphql_response_nested():
    resp = GraphQLResponse({"data": {"user": {"posts": [{"title": "Hello"}]}}})
    assert resp.get("user.posts") == [{"title": "Hello"}]


def test_graphql_response_default():
    resp = GraphQLResponse({"data": {}})
    assert resp.get("missing.path", "default") == "default"


def test_graphql_response_to_dict():
    raw = {"data": {"x": 1}, "errors": []}
    resp = GraphQLResponse(raw)
    assert resp.to_dict() == raw


def test_graphql_client_init():
    client = GraphQLClient("https://api.example.com/graphql",
                           headers={"Authorization": "Bearer token"})
    assert client.endpoint == "https://api.example.com/graphql"
    assert "Authorization" in client.headers


def test_graphql_response_extensions():
    resp = GraphQLResponse({"data": {}, "extensions": {"cache": "hit"}})
    assert resp.extensions["cache"] == "hit"


def test_query_builder_no_name():
    qb = QueryBuilder("query")
    qb.add_field("users", subfields=["id", "name"])
    query = qb.build()
    assert "query {" in query or "query{" in query


def test_query_builder_empty():
    qb = QueryBuilder("query")
    query = qb.build()
    assert "query" in query
    assert "{" in query
    assert "}" in query

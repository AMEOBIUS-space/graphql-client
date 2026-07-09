# GraphQL Client

> Query builder, fragments, variables, and response handling

## Features

- **QueryBuilder** — programmatic query/mutation/subscription building
- **GraphQLVariable** — typed variables with required/default support
- **GraphQLFragment** — reusable field selections
- **GraphQLClient** — execute queries via HTTP POST
- **GraphQLResponse** — parse data/errors, dot-notation access
- Introspection query support

## Quick Start

```python
from client import QueryBuilder, GraphQLClient

qb = QueryBuilder("query", "GetUser")
qb.add_variable("id", "ID!", required=True)
qb.add_field("user", args={"id": "$id"}, subfields=["id", "name", "email"])

client = GraphQLClient("https://api.example.com/graphql", headers={"Authorization": "Bearer token"})
response = client.execute_query(qb, variables={"id": "123"})

resp = GraphQLResponse(response)
print(resp.get("user.name"))
```

## Tests

```bash
python -m pytest tests/ -v
```

## License

MIT

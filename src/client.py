"""GraphQL Client — query builder, fragments, variables, and response handling."""
import json
import urllib.request
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict, field


@dataclass
class GraphQLVariable:
    name: str
    type: str
    default: Optional[str] = None
    required: bool = False

    def declaration(self) -> str:
        suffix = "!" if self.required else ""
        default = f" = {self.default}" if self.default else ""
        return f"${self.name}: {self.type}{suffix}{default}"


@dataclass
class GraphQLFragment:
    name: str
    type: str
    fields: List[str]

    def render(self) -> str:
        return f"fragment {self.name} on {self.type} {{\n  " + "\n  ".join(self.fields) + "\n}"


class QueryBuilder:
    """Build GraphQL queries programmatically."""

    def __init__(self, operation: str = "query", name: str = ""):
        self.operation = operation  # query, mutation, subscription
        self.name = name
        self.variables: List[GraphQLVariable] = []
        self.fields: List[str] = []
        self._fragments: List[GraphQLFragment] = []
        self._args: Dict[str, str] = {}

    def add_variable(self, name: str, type: str, required: bool = False,
                     default: str = None) -> "QueryBuilder":
        self.variables.append(GraphQLVariable(name=name, type=type,
                                               required=required, default=default))
        return self

    def add_field(self, field: str, args: Dict[str, str] = None,
                  subfields: List[str] = None) -> "QueryBuilder":
        if args:
            arg_str = ", ".join(f"{k}: {v}" for k, v in args.items())
            field = f"{field}({arg_str})"
        if subfields:
            field += " {\n  " + "\n  ".join(subfields) + "\n}"
        self.fields.append(field)
        return self

    def add_fragment(self, fragment: GraphQLFragment) -> "QueryBuilder":
        self._fragments.append(fragment)
        self.fields.append(f"...{fragment.name}")
        return self

    def build(self) -> str:
        parts = [self.operation]
        if self.name:
            parts.append(self.name)
        if self.variables:
            var_decls = ", ".join(v.declaration() for v in self.variables)
            parts.append(f"({var_decls})")
        parts.append("{")

        for field in self.fields:
            parts.append(f"  {field}")

        parts.append("}")

        for frag in self._fragments:
            parts.append("\n" + frag.render())

        return " ".join(parts[:3]) + "\n" + "\n".join(parts[3:])


class GraphQLClient:
    """Execute GraphQL queries against an endpoint."""

    def __init__(self, endpoint: str, headers: Dict[str, str] = None,
                 timeout: int = 30):
        self.endpoint = endpoint
        self.headers = headers or {}
        self.timeout = timeout

    def execute(self, query: str, variables: Dict = None,
                operation_name: str = None) -> Dict:
        """Execute a GraphQL query and return the response."""
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        if operation_name:
            payload["operationName"] = operation_name

        data = json.dumps(payload).encode()
        headers = {"Content-Type": "application/json", **self.headers}

        req = urllib.request.Request(self.endpoint, data=data, method="POST",
                                     headers=headers)
        resp = urllib.request.urlopen(req, timeout=self.timeout)
        return json.loads(resp.read().decode())

    def execute_query(self, builder: QueryBuilder,
                      variables: Dict = None) -> Dict:
        """Execute a QueryBuilder."""
        return self.execute(builder.build(), variables)

    def introspect(self) -> Dict:
        """Run introspection query to get schema."""
        query = """
        {
          __schema {
            queryType { name }
            mutationType { name }
            types {
              name
              kind
              fields {
                name
                type { name kind ofType { name kind } }
              }
            }
          }
        }"""
        return self.execute(query)


class GraphQLResponse:
    """Parse and validate GraphQL responses."""

    def __init__(self, raw: Dict):
        self.raw = raw
        self.data = raw.get("data")
        self.errors = raw.get("errors", [])
        self.extensions = raw.get("extensions", {})

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0

    @property
    def has_data(self) -> bool:
        return self.data is not None

    def error_messages(self) -> List[str]:
        return [e.get("message", "") for e in self.errors]

    def get(self, path: str, default: Any = None) -> Any:
        """Get nested value via dot notation: 'user.profile.name'."""
        keys = path.split(".")
        current = self.data
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current

    def to_dict(self) -> Dict:
        return self.raw

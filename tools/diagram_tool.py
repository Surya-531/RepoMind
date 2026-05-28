def generate_mermaid_diagram(files: list[str]) -> str:
    """Generate a Mermaid architecture diagram from path-level architecture signals."""
    paths = " ".join(files)

    if "src/components" in paths:
        return """```mermaid
graph TD
    User[User] --> Frontend[Frontend App]
    Frontend --> Components[UI Components]
    Components --> API[API Layer]
    API --> Database[(Database)]
```"""

    if "controllers" in paths and "models" in paths:
        return """```mermaid
graph TD
    Client[Client] --> Routes[Routes]
    Routes --> Controllers[Controllers]
    Controllers --> Models[Models]
    Models --> Database[(Database)]
```"""

    if "services" in paths and "routes" in paths:
        return """```mermaid
graph TD
    Client[Client] --> Routes[Routes]
    Routes --> Services[Services]
    Services --> Data[Data Access]
    Data --> Database[(Database)]
```"""

    if "apps/" in paths and "packages/" in paths:
        return """```mermaid
graph TD
    Apps[Applications] --> Shared[Shared Packages]
    Apps --> Services[Services]
    Services --> Data[Data Layer]
    Shared --> Tooling[Build and Tooling]
```"""

    return """```mermaid
graph TD
    Repository[Repository] --> Source[Source Code]
    Repository --> Config[Configuration]
    Source --> Runtime[Runtime Entry Points]
    Runtime --> External[External Services]
```"""

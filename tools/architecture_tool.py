def analyze_project_structure(files: list[str]) -> dict:
    """
    Analyze repository structure and detect architecture-level engineering patterns.
    """

    structure = {
        "frontend": False,
        "backend": False,
        "database": False,
        "api": False,
        "testing": False,
        "docker": False,
        "ci_cd": False,
        "microservices": False,
        "monorepo": False,
    }

    for file in files:
        f = file.replace("\\", "/").lower()

        if any(
            signal in f
            for signal in [
                "ui/",
                "components/",
                "pages/",
                "app/",
                "streamlit",
                ".tsx",
                ".jsx",
                "tailwind",
                "next.config",
                "vite.config",
            ]
        ):
            structure["frontend"] = True

        backend_path_signal = any(
            signal in f
            for signal in [
                "controllers/",
                "routes/",
                "services/",
                "server/",
                "middleware/",
                "api/",
                "requirements.txt",
            ]
        )
        backend_language_signal = f.endswith((".py", ".java", ".go", ".cs", ".php"))

        if backend_path_signal or backend_language_signal:
            structure["backend"] = True

        if any(
            signal in f
            for signal in [
                "prisma",
                "schema.sql",
                "mongodb",
                "postgres",
                "mysql",
                "sequelize",
                "typeorm",
            ]
        ):
            structure["database"] = True

        if any(signal in f for signal in ["api/", "routes/", "controller"]):
            structure["api"] = True

        if any(
            signal in f
            for signal in ["test", "spec", "__tests__", "jest", "cypress", "playwright"]
        ):
            structure["testing"] = True

        if "dockerfile" in f or "docker-compose" in f:
            structure["docker"] = True

        if ".github/workflows" in f:
            structure["ci_cd"] = True

        if "apps/" in f and "packages/" in f:
            structure["monorepo"] = True

        if "microservice" in f or "gateway" in f:
            structure["microservices"] = True

    return structure

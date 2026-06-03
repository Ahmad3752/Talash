"""Role-specific developer scoring requirements."""

ROLE_REQUIREMENTS = {
    "backend": {
        "languages": {"python", "java", "javascript", "typescript", "go", "php", "c#"},
        "frameworks": {"fastapi", "django", "flask", "express", "spring", "spring boot", "node.js", "nodejs"},
        "databases": {"postgresql", "postgres", "mysql", "mongodb", "redis", "sqlite"},
        "practices": {"api", "rest", "authentication", "security", "scalability"},
    },
    "frontend": {
        "languages": {"javascript", "typescript", "html", "css"},
        "frameworks": {"react", "vue", "angular", "next.js", "nextjs"},
        "databases": set(),
        "practices": {"api", "performance", "documentation"},
    },
    "full_stack": {
        "languages": {"javascript", "typescript", "python", "java", "html", "css"},
        "frameworks": {"react", "next.js", "nextjs", "node.js", "nodejs", "express", "fastapi", "django"},
        "databases": {"postgresql", "postgres", "mysql", "mongodb", "sqlite"},
        "practices": {"api", "rest", "authentication", "security"},
    },
    "mobile": {
        "languages": {"kotlin", "swift", "dart", "javascript", "typescript"},
        "frameworks": {"flutter", "react native"},
        "databases": {"firebase", "sqlite"},
        "practices": {"api", "performance"},
    },
    "ai_ml": {
        "languages": {"python", "r", "sql"},
        "frameworks": {"tensorflow", "pytorch", "scikit-learn", "pandas", "numpy"},
        "databases": {"postgresql", "mysql", "mongodb"},
        "practices": {"documentation", "performance"},
    },
    "devops": {
        "languages": {"python", "go", "bash", "sql"},
        "frameworks": set(),
        "databases": {"postgresql", "mysql", "redis"},
        "practices": {"security", "scalability", "documentation"},
    },
    "data_engineer": {
        "languages": {"python", "sql", "scala", "java"},
        "frameworks": {"pandas", "numpy"},
        "databases": {"postgresql", "mysql", "mongodb", "redis"},
        "practices": {"api", "performance", "documentation"},
    },
    "qa_automation": {
        "languages": {"python", "java", "javascript", "typescript"},
        "frameworks": {"selenium", "playwright", "cypress", "pytest", "junit"},
        "databases": {"sql", "mysql", "postgresql"},
        "practices": {"documentation", "api"},
    },
}

"""Shared constants for developer CV evaluation."""

EVALUATION_TRACK_RESEARCHER = "researcher"
EVALUATION_TRACK_DEVELOPER = "developer"

ALLOWED_EVALUATION_TRACKS = {
    EVALUATION_TRACK_RESEARCHER,
    EVALUATION_TRACK_DEVELOPER,
}

DEVELOPER_ROLES = {
    "backend": "Backend Developer",
    "frontend": "Frontend Developer",
    "full_stack": "Full Stack Developer",
    "mobile": "Mobile Developer",
    "ai_ml": "AI/ML Engineer",
    "devops": "DevOps Engineer",
    "data_engineer": "Data Engineer",
    "qa_automation": "QA Automation Engineer",
}

ALLOWED_DEVELOPER_ROLES = set(DEVELOPER_ROLES.keys())

DEVELOPER_SCORE_WEIGHTS = {
    "technical_skill_match": 25,
    "project_work_evidence": 25,
    "professional_experience": 15,
    "engineering_practices": 15,
    "role_specific_fit": 10,
    "education_certifications": 5,
    "cv_quality": 5,
}


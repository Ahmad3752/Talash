from db_connect import get_session
from db_models import (
    Book,
    Candidate,
    Education,
    Experience,
    Patent,
    Publication,
    Skill,
    SupervisedStudent,
)
from sqlalchemy import func
from uuid import uuid4


def _normalize_name(name: str | None) -> str | None:
    if not name:
        return None
    normalized = " ".join(name.strip().split()).lower()
    return normalized or None


def database_storage(state: dict) -> dict:
    if state.get("error") or not state.get("all_results"):
        return {}

    session = get_session()
    stored_ids = []

    try:
        for data in state["all_results"]:
            if "error" in data:
                print(f"Skipping {data.get('_candidate_id')} - extraction failed")
                continue

            info = data["personal_info"]
            source_label = data.get("_candidate_id")
            normalized_name = _normalize_name(info.get("name"))

            if normalized_name:
                duplicate = (
                    session.query(Candidate)
                    .filter(func.lower(func.trim(Candidate.name)) == normalized_name)
                    .first()
                )
                if duplicate:
                    print(
                        f"Skipping duplicate candidate by name: {info.get('name')} "
                        f"(existing id={duplicate.id}, candidate_id={duplicate.candidate_id})"
                    )
                    continue

            # Always create a new candidate row to avoid cross-upload overwrites
            # when parser labels repeat (e.g., cv_1 appears in many uploads).
            candidate = Candidate(
                candidate_id=f"tmp_{uuid4().hex}",
                name=info.get("name"),
                email=info.get("email"),
                phone=info.get("phone"),
            )
            session.add(candidate)
            session.flush()

            # Stable monotonic external ID: cv_1, cv_2, cv_3, ...
            candidate.candidate_id = f"cv_{candidate.id}"
            session.flush()

            """degree_level_map = {
                "ssc": "school",
                "hssc": "school",
                "bs": "undergrad",
                "bsc": "undergrad",
                "be": "undergrad",
                "ms": "postgrad",
                "msc": "postgrad",
                "mphil": "postgrad",
                "mba": "postgrad",
                "phd": "doctorate",
            }"""
            degree_level_map = {
                # School
                "ssc": "school", "ssic": "school", "hssc": "school", 
                "matric": "school", "intermediate": "school", "ics": "school",
                
                # Undergraduate
                "bs": "undergrad", "bsc": "undergrad", "be": "undergrad",
                "b.e": "undergrad", "b.s": "undergrad", "b.eng": "undergrad",
                "b.tech": "undergrad", "bachelor": "undergrad",
                "b.arch": "undergrad", "diploma": "undergrad",
                
                # Postgraduate
                "ms": "postgrad", "msc": "postgrad", "mphil": "postgrad",
                "mba": "postgrad", "m.engg": "postgrad", "m.eng": "postgrad",
                "master": "postgrad", "m.s": "postgrad", "me": "postgrad",
                "m.tech": "postgrad", "m.arch": "postgrad", "pgdip": "postgrad",
                
                # Doctorate
                "phd": "doctorate", "ph.d": "doctorate", "d.sc": "doctorate",
                "d.phil": "doctorate", "dphil": "doctorate",
            }

            for edu in data.get("education", []):
                deg = (edu.get("degree") or "").lower()
                level = degree_level_map.get(deg.split()[0] if deg else "", "other")

                board = edu.get("board")
                institution = edu.get("institution")
                if level == "school" and not board and institution:
                    board = institution
                    institution = None
                    print(
                        f"[education] normalized school record: degree={edu.get('degree')} "
                        f"board set from institution"
                    )

                session.add(
                    Education(
                        candidate_id=candidate.id,
                        degree=edu.get("degree"),
                        degree_level=level,
                        field=edu.get("field"),
                        institution=institution,
                        start_year=edu.get("start_year"),
                        end_year=edu.get("end_year"),
                        cgpa=edu.get("cgpa"),
                        cgpa_scale=edu.get("cgpa_scale"),
                        percentage=edu.get("percentage"),
                        board=board,
                        normalized_percentage=edu.get("normalized_percentage"),
                    )
                )

            for exp in data.get("experience", []):
                session.add(
                    Experience(
                        candidate_id=candidate.id,
                        company=exp.get("company"),
                        role=exp.get("role"),
                        employment_type=exp.get("employment_type"),
                        start_date=exp.get("start_date"),
                        end_date=exp.get("end_date"),
                        description=exp.get("description"),
                    )
                )

            for skill_name in data.get("skills", []):
                if skill_name:
                    inferred_flag = not bool(data.get("_skills_from_cv", True))
                    session.add(
                        Skill(
                            candidate_id=candidate.id,
                            skill_name=skill_name,
                            inferred=inferred_flag,
                        )
                    )
            print(
                f"[skills] stored {len(data.get('skills', []))} skill(s), "
                f"_skills_from_cv={data.get('_skills_from_cv', True)}"
            )

            for pub in data.get("publications", []):
                session.add(
                    Publication(
                        candidate_id=candidate.id,
                        pub_type=pub.get("type", "journal"),
                        title=pub.get("title"),
                        venue=pub.get("venue"),
                        issn=pub.get("issn"),
                        year=pub.get("year"),
                        authors=", ".join(pub.get("authors", [])) or None,
                        authorship_role=pub.get("authorship_role"),
                        doi=pub.get("doi"),
                        publisher=pub.get("publisher"),
                        journal_name=pub.get("journal_name"),
                        conference_name=pub.get("conference_name"),
                        conference_maturity=pub.get("conference_maturity"),
                        proceedings_publisher=pub.get("proceedings_publisher"),
                        wos_indexed=pub.get("wos_indexed"),
                        scopus_indexed=pub.get("scopus_indexed"),
                        quartile=pub.get("quartile"),
                        impact_factor=pub.get("impact_factor"),
                        core_rank=pub.get("core_rank"),
                        indexed_in=pub.get("indexed_in"),
                    )
                )

            for book in data.get("books", []):
                session.add(
                    Book(
                        candidate_id=candidate.id,
                        title=book.get("title"),
                        authors=", ".join(book.get("authors", [])) or None,
                        isbn=book.get("isbn"),
                        publisher=book.get("publisher"),
                        year=book.get("year"),
                        url=book.get("url"),
                        authorship_role=book.get("authorship_role"),
                    )
                )

            for patent in data.get("patents", []):
                session.add(
                    Patent(
                        candidate_id=candidate.id,
                        patent_number=patent.get("patent_number"),
                        title=patent.get("title"),
                        year=patent.get("year"),
                        inventors=", ".join(patent.get("inventors", [])) or None,
                        country=patent.get("country"),
                        verification_url=patent.get("verification_url"),
                    )
                )

            for sup in data.get("supervised_students", []):
                session.add(
                    SupervisedStudent(
                        candidate_id=candidate.id,
                        student_name=sup.get("student_name"),
                        level=sup.get("level"),
                        role=sup.get("role"),
                        graduation_year=sup.get("graduation_year"),
                    )
                )

            stored_ids.append(candidate.id)
            print(
                f"Stored candidate from {source_label} as {candidate.candidate_id} "
                f"(db_id={candidate.id})"
            )

        session.commit()
        print(f"Stored {len(stored_ids)} candidate(s) -> IDs: {stored_ids}")
    except Exception as e:
        session.rollback()
        print(f"DB error: {e}")
        raise
    finally:
        session.close()

    return {}

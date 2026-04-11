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

            existing = None
            if info.get("email"):
                existing = session.query(Candidate).filter_by(email=info["email"]).first()

            if existing:
                candidate = existing
                print(f"Updating existing candidate: {info.get('name')}")
            else:
                candidate = Candidate(
                    name=info.get("name"),
                    email=info.get("email"),
                    phone=info.get("phone"),
                    source_pdf=data.get("_candidate_id"),
                )
                session.add(candidate)
                session.flush()
                print(f"New candidate: {info.get('name')} -> id={candidate.id}")

            for edu in data.get("education", []):
                session.add(
                    Education(
                        candidate_id=candidate.id,
                        degree=edu.get("degree"),
                        field=edu.get("field"),
                        institution=edu.get("institution"),
                        start_year=edu.get("start_year"),
                        end_year=edu.get("end_year"),
                        cgpa=edu.get("cgpa"),
                        cgpa_scale=edu.get("cgpa_scale"),
                        percentage=edu.get("percentage"),
                        board=edu.get("board"),
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
                    session.add(Skill(candidate_id=candidate.id, skill_name=skill_name))

            for pub in data.get("publications", []):
                session.add(
                    Publication(
                        candidate_id=candidate.id,
                        type=pub.get("type"),
                        title=pub.get("title"),
                        venue=pub.get("venue"),
                        issn=pub.get("issn"),
                        year=pub.get("year"),
                        authors=", ".join(pub.get("authors", [])) or None,
                        authorship_role=pub.get("authorship_role"),
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

        session.commit()
        print(f"Stored {len(stored_ids)} candidate(s) -> IDs: {stored_ids}")
    except Exception as e:
        session.rollback()
        print(f"DB error: {e}")
        raise
    finally:
        session.close()

    return {}

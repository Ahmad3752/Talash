import os

import fitz


def detect_cv_boundaries(pages: list[str]) -> list[str]:
    """
    pages  : list of per-page text strings (already split on \f)
    returns: list of CV text blocks, each being one candidate's full text.

    Logic:
      - blank page  -> signals end of current CV
      - content page -> accumulate into current CV
    """
    cvs = []
    current_cv_pages = []

    for page in pages:
        clean = page.strip()

        if not clean:
            if current_cv_pages:
                cvs.append("\n\n".join(current_cv_pages))
                current_cv_pages = []
        else:
            current_cv_pages.append(clean)

    if current_cv_pages:
        cvs.append("\n\n".join(current_cv_pages))

    return cvs


def parser(state: dict) -> dict:
    path = state["pdf_path"]
    raw_texts = []

    try:
        if os.path.isdir(path):
            pdf_files = sorted(f for f in os.listdir(path) if f.endswith(".pdf"))
            print(f"Folder mode - {len(pdf_files)} PDF(s) found")
            for fname in pdf_files:
                fpath = os.path.join(path, fname)
                doc = fitz.open(fpath)
                pages = [page.get_text() for page in doc]
                doc.close()
                cvs = detect_cv_boundaries(pages)
                print(f"{fname} -> {len(cvs)} CV(s) detected")
                for i, cv_text in enumerate(cvs):
                    label = f"{os.path.splitext(fname)[0]}_cv{i + 1}"
                    raw_texts.append((label, cv_text))

        elif os.path.isfile(path):
            doc = fitz.open(path)
            pages = [page.get_text() for page in doc]
            doc.close()
            cvs = detect_cv_boundaries(pages)
            for i, cv_text in enumerate(cvs):
                label = f"cv_{i + 1}"
                raw_texts.append((label, cv_text))
        else:
            return {"error": f"Path not found: {path}"}

        if not raw_texts:
            return {"error": "No CV text could be extracted"}

        return {"raw_texts": raw_texts, "error": None}

    except Exception as e:
        return {"error": f"Parsing failed: {str(e)}"}

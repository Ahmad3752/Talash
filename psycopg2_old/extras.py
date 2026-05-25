"""Minimal psycopg2.extras compatibility layer."""

def register_uuid(*args, **kwargs):
    return None


def register_hstore(*args, **kwargs):
    return None


class HstoreAdapter:
    @staticmethod
    def get_oids(*args, **kwargs):
        return None

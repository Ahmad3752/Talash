"""
Admin CLI for clearing the Redis CV deduplication cache.

The scoring pipeline skips a CV when Redis contains its content hash under
cv_hash:<sha256>. This utility scans and deletes only those cv_hash:* keys so
already uploaded CVs can be reprocessed without touching other Redis data.

Usage:
  python -m talash.reset_cv_hash_cache
  python -m talash.reset_cv_hash_cache --confirm
"""

from __future__ import annotations

import argparse
import sys

from .redis_cache import (
    CV_HASH_PATTERN,
    clear_cv_hash_cache,
    count_cv_hash_cache,
    ping,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Clear only Redis CV hash cache keys used for deduplication.",
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Actually delete matching keys. Without this flag, only counts them.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=500,
        help="SCAN/DELETE batch size. Default: 500.",
    )
    args = parser.parse_args(argv)

    if args.batch_size <= 0:
        parser.error("--batch-size must be greater than 0")

    if not ping():
        print("Redis is not reachable. Check REDIS_URL or start the Redis service.", file=sys.stderr)
        return 2

    before = count_cv_hash_cache(batch_size=args.batch_size)
    print(f"Matched {before} Redis key(s) with pattern {CV_HASH_PATTERN!r}.")

    if not args.confirm:
        print("Dry run only. Re-run with --confirm to delete these keys.")
        return 0

    deleted = clear_cv_hash_cache(batch_size=args.batch_size)
    after = count_cv_hash_cache(batch_size=args.batch_size)
    print(f"Deleted {deleted} key(s). Remaining matching keys: {after}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

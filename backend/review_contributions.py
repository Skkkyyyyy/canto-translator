"""Read what users have submitted.

    python review_contributions.py              # pending only
    python review_contributions.py --all        # every status
    python review_contributions.py --csv        # dump as CSV for a spreadsheet

Approving is still manual: copy the row into data/tokens100.csv, then
UPDATE contributions SET status='approved' WHERE id='...';
"""

import argparse
import csv
import sys

from db import connect, init_db

FIELDS = ["id", "created_at", "kind", "intent", "token", "cantonese",
          "mandarin", "english", "function", "example", "note", "contributor", "status"]


def fetch(status: str | None):
    query = "SELECT * FROM contributions"
    params: tuple = ()
    if status:
        query += " WHERE status = ?"
        params = (status,)
    query += " ORDER BY created_at DESC"
    with connect() as conn:
        return [dict(row) for row in conn.execute(query, params)]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true", help="include reviewed rows")
    parser.add_argument("--csv", action="store_true", help="print CSV instead of a summary")
    args = parser.parse_args()

    init_db()
    rows = fetch(None if args.all else "pending")

    if args.csv:
        writer = csv.DictWriter(sys.stdout, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
        return

    if not rows:
        print("No submissions yet.")
        return

    print(f"{len(rows)} submission(s)\n")
    for row in rows:
        print(f"[{row['status']}] {row['id']}  {row['created_at'][:19]}  ({row['kind']}/{row['intent']})")
        print(f"  {row['token']}")
        print(f"  廣東話 {row['cantonese'] or '—'} | 普通话 {row['mandarin'] or '—'} | EN {row['english'] or '—'}")
        if row["function"]:
            print(f"  function: {row['function']}")
        if row["example"]:
            print(f"  example:  {row['example']}")
        if row["note"]:
            print(f"  note:     {row['note']}")
        if row["source_text"]:
            print(f"  typed:    {row['source_text']}")
        if row["contributor"]:
            print(f"  from:     {row['contributor']}")
        print()


if __name__ == "__main__":
    main()

"""Merge papers from decker list.txt into the seed JSON, skipping duplicates."""
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SOURCE_PATH = ROOT / "decker list.txt"
SEED_PATH = ROOT / "data" / "seed_papers.json"


SOURCE_MAP = {
    "AER": "AER",
    "QJE": "QJE",
    "JPE": "JPE",
    "ECTA": "Econometrica",
    "REStud": "REStud",
    "JEP": "Journal of Economic Perspectives",
    "JET": "JET",
    "JFE": "Journal of Financial Economics",
    "JoF": "Journal of Finance",
    "AMM": "American Mathematical Monthly",
    "JEH": "Journal of Economic History",
    "BIS": "BIS",
    "WP": "Working Paper",
}


FIELD_RULES = [
    ("Urban", ["city", "road", "congestion", "transport", "zoning", "berlin wall", "urban"]),
    ("Development", ["development", "india", "congo", "agriculture", "irrigation", "brazil"]),
    ("Growth", ["growth", "ideas", "productivity slowdown", "population", "mechanics of economic development"]),
    ("Macroeconomics", ["inflation", "demand", "debt", "hank", "social discount", "economic growth"]),
    ("Labour", ["labor", "labour", "women earn", "career", "unemployment", "mobility", "bus and train"]),
    ("Public Finance", ["tax", "insurance", "snap", "food stamp", "fiscal", "pricing", "benefits"]),
    ("IO", ["competition", "market power", "bargaining", "oligopoly", "pricing", "joint venture", "acquisitions", "monopoly", "collude", "used-car", "dialysis", "cereal"]),
    ("Finance", ["auction", "reserve prices", "bid, ask", "traders", "bargaining problem"]),
    ("Political Economy", ["colonial", "state", "revolutions", "conflict", "culture war", "gender roles"]),
    ("Health", ["medicare", "ivf", "worms", "pharmaceutical"]),
    ("Media", ["news", "media", "cable", "newspapers", "persuasion"]),
    ("Econometrics", ["instrumental variable", "difference-in-differences", "estimating", "hypothesis generation"]),
    ("Behavioural", ["risk aversion", "herd behavior", "diversification bias", "lemons"]),
    ("Trade", ["railroads", "ricardo", "technology adoption", "spillovers", "face-to-face"]),
]


def normalize_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def clean_source(raw_source: str) -> str:
    source = raw_source.strip().strip(",")
    source = re.sub(r"\([^)]*\)", "", source).strip().strip(",")
    if not source:
        return ""
    return SOURCE_MAP.get(source, source)


def infer_type(year: int | None, source: str) -> str:
    if source in {"Working Paper", "NBER", "CEPR"}:
        return "working"
    if year and year >= 2015:
        return "modern"
    return "classic"


def infer_field(title: str) -> str:
    title_lower = title.lower()
    for field, keywords in FIELD_RULES:
        if any(keyword in title_lower for keyword in keywords):
            return field
    return "General"


def parse_entry(entry: str) -> dict:
    title_match = re.match(
        r"(?P<authors>.+?),\s*“(?P<title>.+?)”(?P<rest>.*)$",
        entry,
        re.DOTALL,
    )
    if not title_match:
        raise ValueError(f"Could not parse entry: {entry}")

    rest = title_match.group("rest")
    year_match = re.search(r"\((\d{4})\)", rest)
    if not year_match:
        raise ValueError(f"Could not parse year: {entry}")

    authors = re.sub(r"\s+", " ", title_match.group("authors")).strip()
    title = re.sub(r"\s+", " ", title_match.group("title")).strip()
    year = int(year_match.group(1))
    source = clean_source(rest[year_match.end():])

    return {
        "title": title,
        "authors": authors,
        "year": year,
        "source": source,
        "field": infer_field(title),
        "type": infer_type(year, source),
        "citation_proxy": 0,
        "url": "",
    }


def main() -> None:
    existing = json.loads(SEED_PATH.read_text())
    existing_titles = {normalize_text(paper["title"]) for paper in existing}

    entries = [entry.strip() for entry in SOURCE_PATH.read_text().split("\n\n") if entry.strip()]
    additions = []

    for entry in entries:
        paper = parse_entry(entry)
        key = normalize_text(paper["title"])
        if key in existing_titles:
            continue
        additions.append(paper)
        existing_titles.add(key)

    if additions:
        existing.extend(additions)
        SEED_PATH.write_text(json.dumps(existing, indent=2, ensure_ascii=True) + "\n")

    print(f"Parsed {len(entries)} entries.")
    print(f"Added {len(additions)} papers.")
    print(f"Seed file now has {len(existing)} papers.")


if __name__ == "__main__":
    main()

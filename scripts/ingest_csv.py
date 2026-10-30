"""
GDGC-JISU1 Learn with Communities — CSV Ingestion Script
=========================================================
Usage:
    python scripts/ingest_csv.py                     # Auto-detect latest CSV in data/raw/
    python scripts/ingest_csv.py path/to/file.csv    # Ingest a specific CSV

This script:
1. Reads the daily CSV from Google
2. Computes derived metrics (pace, at-risk status, track type)
3. Writes data/latest.json (current snapshot for the dashboard)
4. Appends to data/history.json (daily aggregates for trend charts)
"""

import csv
import json
import os
import sys
import re
from datetime import datetime, date
from pathlib import Path

# ── Configuration ──────────────────────────────────────────────────────────
DEADLINE = date(2026, 11, 23)
TOTAL_BADGES_REQUIRED = 10
DAILY_LAB_LIMIT = 15
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
LATEST_JSON = DATA_DIR / "latest.json"
HISTORY_JSON = DATA_DIR / "history.json"

# ── Student Curriculum (10 Skill Badges) ───────────────────────────────────
STUDENT_CURRICULUM = [
    {"name": "The Basics of Google Cloud Compute",                             "url": "https://www.skills.google/course_templates/754",  "credits": 4},
    {"name": "Configure Service Accounts and IAM Roles for Google Cloud",      "url": "https://www.skills.google/course_templates/702",  "credits": 4},
    {"name": "Implement Speech and Language Solutions with Pre-trained APIs",   "url": "https://www.skills.google/course_templates/700",  "credits": 4},
    {"name": "Develop AI-Powered Prototypes in Google AI Studio",              "url": "https://www.skills.google/course_templates/1426", "credits": 0},
    {"name": "Analyze Images with the Cloud Vision API",                       "url": "https://www.skills.google/course_templates/633",  "credits": 12},
    {"name": "Build a Website on Google Cloud",                                "url": "https://www.skills.google/course_templates/638",  "credits": 13},
    {"name": "Create Your First Gemini Enterprise Application",                "url": "https://www.skills.google/course_templates/1586", "credits": 0},
    {"name": "Store, Process, and Manage Data on Google Cloud - Console",      "url": "https://www.skills.google/course_templates/658",  "credits": 3},
    {"name": "Using the Google Cloud Speech API",                              "url": "https://www.skills.google/course_templates/756",  "credits": 4},
    {"name": "Explore Generative AI in Agent Platform",                        "url": "https://www.skills.google/course_templates/959",  "credits": 16},
]
TOTAL_CREDITS = sum(b["credits"] for b in STUDENT_CURRICULUM)

def norm_name(s: str) -> str:
    return re.sub(r'[^a-z0-9]', '', s.lower())

def match_curriculum(badge_list: list[str]):
    """Match completed badges against the Student curriculum."""
    completed = []
    pending = []
    
    earned_norm = {norm_name(b): b for b in badge_list}
    
    for item in STUDENT_CURRICULUM:
        target = norm_name(item["name"])
        # Check direct or partial match
        matched = any(target in en or en in target for en in earned_norm.keys())
        if matched:
            completed.append(item)
        else:
            pending.append(item)
            
    credits_needed = sum(item["credits"] for item in pending)
    credits_spent = sum(item["credits"] for item in completed)
    return completed, pending, credits_spent, credits_needed


def detect_track(access_code: str) -> str:
    """Determine if a participant is on the Student or Developer track."""
    if "EDUCR" in access_code:
        return "Student"
    elif "DEVBR" in access_code:
        return "Developer"
    return "Unknown"


def extract_date_from_filename(filename: str) -> str:
    """Try to extract a date from the CSV filename."""
    # Pattern: GDGC-JISU1 [30 Oct].csv or GDGC-JISU1_2026-10-30.csv
    match = re.search(r'\[(\d{1,2}\s+\w+)\]', filename)
    if match:
        try:
            day_month = match.group(1)
            parsed = datetime.strptime(f"{day_month} 2026", "%d %b %Y")
            return parsed.strftime("%Y-%m-%d")
        except ValueError:
            pass
    
    match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
    if match:
        return match.group(1)
    
    return date.today().isoformat()


def find_latest_csv() -> Path:
    """Find the most recently modified CSV in data/raw/."""
    csvs = list(RAW_DIR.glob("*.csv"))
    if not csvs:
        print(f"❌ No CSV files found in {RAW_DIR}")
        print(f"   Drop your daily CSV there and re-run this script.")
        sys.exit(1)
    
    # Sort by modification time, newest first
    csvs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return csvs[0]


def parse_csv(csv_path: Path) -> list[dict]:
    """Parse the Google Learn with Communities CSV into structured data."""
    participants = []
    
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            name = row.get("User Name", "").strip()
            email = row.get("User Email", "").strip()
            badges_count = int(row.get("Skill Badges Completed Count", "0").strip() or "0")
            badges_names = row.get("Skill Badges Completed Names", "").strip()
            access_code = row.get("Access Code", "")
            redemption = row.get("Access Code Redemption Status", "No").strip()
            milestone = row.get("Milestone Completed", "No Milestone").strip()
            profile_url = row.get("Google Skills Profile URL", "").strip()
            profile_status = row.get("Google Skills Profile Status", "").strip()
            dev_profile_url = row.get("Google Developer Profile URL", "").strip()
            dev_profile_status = row.get("Google Developer Profile Status", "").strip()
            gear_badges = row.get("GEAR Digital Badges", "").strip()
            
            track = detect_track(access_code)
            
            # Calculate days remaining and required pace
            today = date.today()
            days_remaining = max(0, (DEADLINE - today).days)
            badges_remaining = max(0, TOTAL_BADGES_REQUIRED - badges_count)
            
            if days_remaining > 0 and badges_remaining > 0:
                pace_needed = round(badges_remaining / days_remaining, 2)
            elif badges_remaining == 0:
                pace_needed = 0  # Already done!
            else:
                pace_needed = float('inf')  # Past deadline
            
            # Determine risk status
            if badges_count >= TOTAL_BADGES_REQUIRED:
                status = "completed"
            elif redemption == "No":
                status = "not_started"
            elif badges_count == 0 and redemption == "Yes":
                status = "redeemed_only"
            elif pace_needed > 1.5:
                status = "at_risk"
            elif pace_needed > 0.8:
                status = "on_track"
            else:
                status = "ahead"
            
            # Completion percentage
            completion_pct = round((badges_count / TOTAL_BADGES_REQUIRED) * 100, 1)
            
            # Parse individual badge names
            badge_list = [b.strip() for b in badges_names.split(",") if b.strip()] if badges_names else []
            comp_curr, pend_curr, cr_spent, cr_needed = match_curriculum(badge_list)
            
            participants.append({
                "name": name,
                "email": email,
                "track": track,
                "profile_url": profile_url,
                "profile_status": profile_status,
                "dev_profile_url": dev_profile_url if dev_profile_url != "Not applicable" else None,
                "dev_profile_status": dev_profile_status if dev_profile_status != "Not applicable" else None,
                "access_code_redeemed": redemption == "Yes",
                "milestone": milestone,
                "gear_badges": gear_badges if gear_badges not in ("Not applicable", "No Badge", "") else None,
                "badges_count": badges_count,
                "badges_names": badge_list,
                "completed_curriculum": comp_curr,
                "pending_curriculum": pend_curr,
                "credits_spent": cr_spent,
                "credits_needed": cr_needed,
                "completion_pct": completion_pct,
                "badges_remaining": badges_remaining,
                "days_remaining": days_remaining,
                "pace_needed": pace_needed if pace_needed != float('inf') else 999,
                "status": status,
            })
    
    # Sort by badges_count descending, then by name
    participants.sort(key=lambda p: (-p["badges_count"], p["name"].lower()))
    
    # Assign ranks
    for i, p in enumerate(participants):
        p["rank"] = i + 1
    
    return participants


def compute_summary(participants: list[dict], report_date: str) -> dict:
    """Compute aggregate stats for the dashboard."""
    total = len(participants)
    
    # Badge distribution: how many people have 0, 1, 2... 10 badges
    badge_distribution = {i: 0 for i in range(TOTAL_BADGES_REQUIRED + 1)}
    for p in participants:
        count = min(p["badges_count"], TOTAL_BADGES_REQUIRED)
        badge_distribution[count] = badge_distribution.get(count, 0) + 1
    
    # Track counts
    students = [p for p in participants if p["track"] == "Student"]
    developers = [p for p in participants if p["track"] == "Developer"]
    
    # Status counts
    status_counts = {}
    for p in participants:
        s = p["status"]
        status_counts[s] = status_counts.get(s, 0) + 1
    
    # Milestone counts
    milestone_counts = {}
    for p in participants:
        m = p["milestone"]
        milestone_counts[m] = milestone_counts.get(m, 0) + 1
    
    redeemed_count = sum(1 for p in participants if p["access_code_redeemed"])
    completed_count = sum(1 for p in participants if p["badges_count"] >= TOTAL_BADGES_REQUIRED)
    at_risk_count = status_counts.get("at_risk", 0)
    not_started_count = status_counts.get("not_started", 0) + status_counts.get("redeemed_only", 0)
    
    days_remaining = max(0, (DEADLINE - date.today()).days)
    
    return {
        "report_date": report_date,
        "generated_at": datetime.now().isoformat(),
        "deadline": DEADLINE.isoformat(),
        "days_remaining": days_remaining,
        "total_participants": total,
        "total_students": len(students),
        "total_developers": len(developers),
        "redeemed_count": redeemed_count,
        "not_redeemed_count": total - redeemed_count,
        "completed_count": completed_count,
        "at_risk_count": at_risk_count,
        "not_started_count": not_started_count,
        "badge_distribution": badge_distribution,
        "status_counts": status_counts,
        "milestone_counts": milestone_counts,
        "avg_badges": round(sum(p["badges_count"] for p in participants) / total, 2) if total else 0,
    }


def update_history(summary: dict):
    """Append today's summary to the history file for trend charts."""
    history = []
    if HISTORY_JSON.exists():
        with open(HISTORY_JSON, "r", encoding="utf-8") as f:
            history = json.load(f)
    
    # Check if we already have an entry for this date
    report_date = summary["report_date"]
    history = [h for h in history if h.get("report_date") != report_date]
    
    # Append new entry
    history_entry = {
        "report_date": report_date,
        "total_participants": summary["total_participants"],
        "redeemed_count": summary["redeemed_count"],
        "completed_count": summary["completed_count"],
        "at_risk_count": summary["at_risk_count"],
        "not_started_count": summary["not_started_count"],
        "avg_badges": summary["avg_badges"],
        "badge_distribution": summary["badge_distribution"],
    }
    history.append(history_entry)
    history.sort(key=lambda h: h["report_date"])
    
    with open(HISTORY_JSON, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)
    
    print(f"📈 History updated ({len(history)} data points)")


def main():
    # Determine which CSV to process
    if len(sys.argv) > 1:
        csv_path = Path(sys.argv[1]).resolve()
        if not csv_path.exists():
            print(f"❌ File not found: {csv_path}")
            sys.exit(1)
    else:
        csv_path = find_latest_csv()
    
    print(f"📂 Processing: {csv_path.name}")
    
    # Extract report date from filename
    report_date = extract_date_from_filename(csv_path.name)
    print(f"📅 Report Date: {report_date}")
    
    # Parse participants
    participants = parse_csv(csv_path)
    print(f"👥 Participants: {len(participants)}")
    
    # Compute summary
    summary = compute_summary(participants, report_date)
    
    # Build the final JSON
    output = {
        "summary": summary,
        "curriculum": STUDENT_CURRICULUM,
        "participants": participants,
    }
    
    # Write latest.json
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(LATEST_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"✅ Written: {LATEST_JSON}")
    
    # Update history
    update_history(summary)
    
    # Print quick stats
    print(f"\n{'═' * 50}")
    print(f"  GDGC-JISU1 Dashboard Summary — {report_date}")
    print(f"{'═' * 50}")
    print(f"  📊 Total Enrolled:     {summary['total_participants']}")
    print(f"  🎓 Students:           {summary['total_students']}")
    print(f"  💻 Developers:         {summary['total_developers']}")
    print(f"  ✅ Completed (10/10):  {summary['completed_count']}")
    print(f"  ⚠️  At Risk:            {summary['at_risk_count']}")
    print(f"  🔑 Code Redeemed:      {summary['redeemed_count']}")
    print(f"  ❌ Not Redeemed:       {summary['not_redeemed_count']}")
    print(f"  📈 Avg Badges:         {summary['avg_badges']}")
    print(f"  ⏰ Days Remaining:     {summary['days_remaining']}")
    print(f"{'═' * 50}")


if __name__ == "__main__":
    main()


# GDGC-JISU1 — Learn with Communities Dashboard 🚀

A progress tracking dashboard for **Google Cloud Learn with Communities 2026** (GDGC-JISU1 community).

## ⚡ Quick Start

### 1. Ingest a CSV
```bash
# Drop your daily CSV into data/raw/, then run:
python scripts/ingest_csv.py

# Or specify a CSV directly:
python scripts/ingest_csv.py "path/to/GDGC-JISU1 [30 Oct].csv"
```

### 2. View Dashboard
```bash
# Start a local server:
python -m http.server 8080

# Open in browser:
# http://localhost:8080
```

## 📚 Student Curriculum (10 Required Skill Badges)

| # | Skill Badge Name | URL | Credits |
|---|---|---|:---:|
| 1 | The Basics of Google Cloud Compute | [Link](https://www.skills.google/course_templates/754) | 4 |
| 2 | Configure Service Accounts and IAM Roles for Google Cloud | [Link](https://www.skills.google/course_templates/702) | 4 |
| 3 | Implement Speech and Language Solutions with Pre-trained APIs | [Link](https://www.skills.google/course_templates/700) | 4 |
| 4 | Develop AI-Powered Prototypes in Google AI Studio | [Link](https://www.skills.google/course_templates/1426) | 0 |
| 5 | Analyze Images with the Cloud Vision API | [Link](https://www.skills.google/course_templates/633) | 12 |
| 6 | Build a Website on Google Cloud | [Link](https://www.skills.google/course_templates/638) | 13 |
| 7 | Create Your First Gemini Enterprise Application | [Link](https://www.skills.google/course_templates/1586) | 0 |
| 8 | Store, Process, and Manage Data on Google Cloud - Console | [Link](https://www.skills.google/course_templates/658) | 3 |
| 9 | Using the Google Cloud Speech API | [Link](https://www.skills.google/course_templates/756) | 4 |
| 10 | Explore Generative AI in Agent Platform | [Link](https://www.skills.google/course_templates/959) | 16 |
| **Total** | **All 10 Badges** | | **60 credits** |

> [!NOTE]
> Every student receives **200 credits**. Completing all 10 badges only takes **60 credits**, leaving **140 spare credits** for lab retries or practice.

## 📥 Daily Update Workflow
1. Download the CSV from your daily Google email
2. Save it to `data/raw/`
3. Run `python scripts/ingest_csv.py`
4. Refresh `http://localhost:8080`

## 📁 Project Structure
```
Learn_with_communities/
├── index.html              # Clean, professional dashboard (HTML/JS/Tailwind)
├── data/
│   ├── raw/                # Drop daily CSVs here
│   ├── latest.json         # Current data + curriculum metadata
│   └── history.json        # Historical snapshots for trend lines
├── scripts/
│   └── ingest_csv.py       # CSV parser & metric processor
└── README.md
```

## 🔑 Key Rules & Constraints
- **Deadline:** 23 November 2026 (No extensions provisioned)
- **Daily Lab Limit:** Maximum 15 labs completed per day
- **Total Badges Required:** 10 Skill Badges
- **Credit Allocation:** 200 credits total per participant

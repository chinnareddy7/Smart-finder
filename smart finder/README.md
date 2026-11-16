# SMART LOST & FOUND – AI POWERED CAMPUS SYSTEM

> **College Mini Project for B.Sc. Computer Science (AI & ML)**  
> A full-stack, automated campus management platform powered by Python Flask, SQLite, and Scikit-learn Machine Learning (TF-IDF Vectorization & Cosine Similarity).

---

## 1. Overview & Problem Statement

College campuses witness hundreds of missing and misplaced personal items every semester (ID cards, scientific calculators, laptops, water bottles, keys, wallets, and textbooks). Traditional physical noticeboards or informal WhatsApp/Telegram groups are noisy, unsearchable, lack privacy protection, and fail to automatically correlate lost reports with found reports.

**Smart Lost & Found** solves this by:
1. Providing a centralized SaaS-style campus reporting portal.
2. Running an **actual Scikit-learn AI Matching Engine** that calculates mathematical similarity scores (0% to 100%) between reported lost and found items.
3. Automatically generating detailed explanations of why items matched (shared TF-IDF n-gram keywords, category alignment, campus location proximity).
4. Protecting private student details (phone, email, roll number) with an **Ownership Claim & Verification Request System** that unlocks contact information only when an item report owner approves the claim.
5. Providing an **Administrator Control Center** for campus safety officers to moderate items, inspect student directories, and track recovery rates.

---

## 2. Technology Stack

- **Backend**:
  - Python 3.12
  - Flask (Modular Blueprints architecture)
  - SQLite3 (Relational database)
  - Flask-SQLAlchemy (ORM)
  - Flask-Login (Session management & user authentication)
  - Werkzeug (Secure SHA-256 password hashing)
  - Custom CSRF Token security middleware

- **Frontend**:
  - HTML5 & CSS3
  - JavaScript (ES6+, real-time image preview, filter clearing, tooltip initialization)
  - Bootstrap 5.3 & Bootstrap Icons
  - Google Fonts (`Inter`)
  - SaaS Palette: Deep Navy (`#0f2444`), Light Blue (`#0284c7`, `#38bdf8`), Soft Grey (`#f8fafc`), Clean White (`#ffffff`)

- **AI / Machine Learning**:
  - **Scikit-learn** (`TfidfVectorizer`, `cosine_similarity`)
  - **NumPy & SciPy**
  - Custom Domain NLP Preprocessing (lowercasing, symbol stripping, campus stopword removal, morphological plural inflection normalization)

---

## 3. Real AI Matching System (The Core Engine)

Unlike mock systems that return random percentages or hardcoded values, this application runs a **genuine Natural Language Processing and Machine Learning pipeline**:

```
[Raw User Input] (Name, Category, Description, Location, Details)
       │
       ▼
[Domain Preprocessing] (Punctuation removal, lowercasing, English stopword elimination, stemming)
       │
       ▼
[TF-IDF Vectorizer] (Sublinear term frequency, unigrams & bigrams: ngram_range=(1, 2))
       │
       ▼
[Cosine Similarity Matrix] (Computes dot product of normalized TF-IDF feature vectors)
       │
       ▼
[Multi-Factor Weighted Scoring Engine]
  ├── Text Cosine Similarity : 60% Weight
  ├── Category Match         : 25% Weight (Exact = 1.0, Compatible = 0.6, Mismatch = 0.0)
  └── Campus Location Proximity: 15% Weight (Same Zone = 1.0, Nearby Overlap = 0.75, Different = 0.1)
       │
       ▼
[Confidence Classification & Threshold Filter]
  ├── Score >= 70%: High Confidence Match (Green Badge)
  ├── 45% - 69%   : Moderate Probability Match (Blue Badge)
  └── 25% - 44%   : Fair Similarity (Amber Badge)
       │
       ▼
[AI Explanation Generator] (Extracts shared token intersection & outputs human-readable justification)
       │
       ▼
[SQLite Storage & Real-Time In-App Notifications]
```

### Real Test Example:
- **Lost Report**: `"I lost my black water bottle in the reading hall. Has NASA space sticker."` (Category: *Water Bottles*, Location: *Central Library*)
- **Found Report**: `"Black water flask found sitting on a library table. Prominent NASA space sticker."` (Category: *Water Bottles*, Location: *Central Library*)
- **AI Engine Output**:
  - Overall Similarity: **55.8%**
  - Text TF-IDF Cosine Score: **26.4%**
  - Category Match: **100% (Exact)**
  - Location Match: **100% (Identical: Central Library)**
  - Matching Keywords: `'black'`, `'bottle'`, `'flask'`, `'nasa'`, `'space'`
  - Explanation: *"Moderate probability match: Category matches exactly (Water Bottles & Flasks). Reported in the identical campus location (Central Library). Key matching terms: 'black', 'bottle', 'flask', 'nasa', 'space'."*

---

## 4. Database Schema (6 Relational Tables)

1. **`users`**:
   - `id`, `student_id` (Unique Roll No), `name`, `email` (Unique), `phone`, `department`, `password_hash`, `is_admin`, `is_active`, `created_at`.
2. **`lost_items`**:
   - `id`, `user_id` (FK -> users.id), `item_name`, `category`, `description`, `location`, `lost_date`, `additional_details`, `image_filename`, `status` (`'Lost'`, `'Recovered'`), `created_at`, `updated_at`.
3. **`found_items`**:
   - `id`, `user_id` (FK -> users.id), `item_name`, `category`, `description`, `location`, `found_date`, `storage_location` (Custody point), `additional_details`, `image_filename`, `status` (`'Found'`, `'Claimed'`), `created_at`, `updated_at`.
4. **`matches`**:
   - `id`, `lost_item_id` (FK), `found_item_id` (FK), `similarity_score`, `text_score`, `category_score`, `location_score`, `category_match`, `location_match`, `explanation`, `status`, `created_at`.
5. **`contact_requests`**:
   - `id`, `sender_id` (FK), `receiver_id` (FK), `item_type`, `lost_item_id`, `found_item_id`, `message` (Proof of claim), `status` (`'Pending'`, `'Accepted'`, `'Rejected'`), `response_note`, `created_at`.
6. **`notifications`**:
   - `id`, `user_id` (FK), `title`, `message`, `notification_type`, `link`, `is_read`, `created_at`.

---

## 5. Project Directory Structure

```
smart finder/
│
├── app.py                      # Flask Application Factory, context processors & error handlers
├── config.py                   # App configurations, upload limits & category constants
├── models.py                   # SQLAlchemy ORM models with relations & cascade constraints
├── seed_data.py                # Realistic campus seed data script
├── run.py                      # One-click execution launcher
├── utils.py                    # CSRF security, file upload UUID handler, admin decorator
├── requirements.txt            # Python dependencies
├── README.md                   # Complete documentation
│
├── ai_engine/                  # Pure Machine Learning Module
│   ├── __init__.py
│   ├── preprocessing.py        # Tokenizer, stop words, stemming
│   └── matching.py             # TF-IDF, Cosine Similarity & synchronization functions
│
├── routes/                     # Blueprint modular route controllers
│   ├── __init__.py
│   ├── auth.py                 # Registration, login, logout, password hashing
│   ├── student.py              # Home page, student dashboard, my reports
│   ├── lost.py                 # Report lost, browse, edit, delete, recover
│   ├── found.py                # Report found, browse, edit, delete, mark claimed
│   ├── matches.py              # AI Match center & recalculate engine
│   ├── requests.py             # Contact requests, claim approvals & privacy disclosure
│   ├── admin.py                # Admin dashboard, student directory, item moderation
│   └── notifications.py        # Notification center & read status toggles
│
├── templates/                  # Jinja2 HTML5 UI Templates
│   ├── base.html               # Master layout with responsive navbar & notification badge
│   ├── index.html              # Modern SaaS landing page with live dynamic statistics
│   ├── login.html              # Sign in with test credentials helper
│   ├── register.html           # Student registration
│   ├── dashboard.html          # Student command center with AI suggested matches
│   ├── report_lost.html        # Report lost item form with live photo preview
│   ├── report_found.html       # Report found item form with custody storage location
│   ├── edit_report.html        # Report edit interface
│   ├── lost_items.html         # Search & filter lost items
│   ├── found_items.html        # Search & filter found items
│   ├── item_details.html       # Detailed view with claim modal & privacy guard
│   ├── my_reports.html         # Tabbed center: Lost, Found, Incoming & Outgoing Claims
│   ├── matches.html            # AI Matching Center with side-by-side comparison
│   ├── admin_dashboard.html    # Admin management panel
│   ├── admin_students.html     # Student directory & account activation controls
│   ├── admin_matches.html      # AI matching analytics & audit logs
│   └── notifications.html      # User notifications
│
├── static/
│   ├── css/
│   │   └── style.css           # Custom SaaS stylesheet (Navy/Light Blue palette)
│   ├── js/
│   │   └── main.js             # Image drag-drop preview & UI utilities
│   ├── uploads/                # Secured student item photo uploads
│   └── images/
│
└── tests/                      # Automated Test Suite (12 Unit & Integration Tests)
    ├── __init__.py
    ├── test_auth.py            # User auth, password hashing, duplicate prevention
    ├── test_matching.py        # Preprocessing, TF-IDF cosine similarity, accuracy
    └── test_reports.py         # Item reporting, AI trigger, claim lifecycle, authorization
```

---

## 6. Installation & Quick Start

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Seed the Database with Demo Campus Data
```bash
python seed_data.py
```
*(This sets up the SQLite database with 6 campus users, realistic lost and found reports, and calculates initial AI TF-IDF matches.)*

### Step 3: Launch the Application

**Option A (Windows 1-Click Launcher):**
Double-click `run.bat` or run:
```cmd
run.bat
```

**Option B (Python Command):**
```bash
python run.py
# or
python app.py
```

Open your browser and navigate to:
**`http://127.0.0.1:5000`**

---

## 7. Demo Accounts for Evaluation

| Role | Student Roll ID / Email | Password | Access Level |
| :--- | :--- | :--- | :--- |
| **Administrator** | `ADMIN001` or `admin@campus.edu` | `AdminPassword123` | Full Admin Dashboard, Moderation, User Directory |
| **Student 1** | `CS202401` or `aarav@campus.edu` | `StudentPassword123` | Reports: Hydro Flask Water Bottle, Logitech Mouse |
| **Student 2** | `EC202415` or `priya@campus.edu` | `StudentPassword123` | Reports: Casio fx-991EX Calculator, Found Wallet |
| **Student 3** | `ME202409` or `rohan@campus.edu` | `StudentPassword123` | Reports: Fossil Wallet, Found Calculator |

---

## 8. Running the Automated Test Suite

To run all 12 unit and integration tests:
```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

Expected output:
```
test_deactivated_account_login_rejection (test_auth.AuthTestCase) ... ok
test_duplicate_registration_prevention (test_auth.AuthTestCase) ... ok
test_successful_registration_and_login (test_auth.AuthTestCase) ... ok
test_user_password_hashing (test_auth.AuthTestCase) ... ok
test_category_and_location_comparison (test_matching.AIMatchingEngineTestCase) ... ok
test_empty_and_special_text_handling (test_matching.AIMatchingEngineTestCase) ... ok
test_high_similarity_matching (test_matching.AIMatchingEngineTestCase) ... ok
test_text_preprocessing (test_matching.AIMatchingEngineTestCase) ... ok
test_unrelated_items_low_similarity (test_matching.AIMatchingEngineTestCase) ... ok
test_contact_request_lifecycle (test_reports.ReportsTestCase) ... ok
test_report_lost_item_and_ai_trigger (test_reports.ReportsTestCase) ... ok
test_unauthorized_edit_prevention (test_reports.ReportsTestCase) ... ok

Ran 12 tests in ~11s
OK
```

---

## 9. Security Implementations

- **Password Hashing**: Werkzeug's PBKDF2 / SHA-256 password hashing. Passwords are never saved in cleartext.
- **CSRF Token Protection**: Session-based cryptographic token verification for all POST form submissions.
- **Privacy Shield**: Contact info (phone, email, student ID) of reporters is hidden from public view. Only unlocked when a report owner approves a claimant's contact request.
- **Role-Based Authorization**: `@admin_required` and `@login_required` route decorators prevent unauthorized students from tampering with moderation endpoints.
- **Safe File Uploads**: Image extensions restricted to `.png`, `.jpg`, `.jpeg`, `.webp`, with randomized UUID renaming to block path traversal and overwriting attacks.
- **SQL Injection Prevention**: SQLAlchemy parameterized queries across all database operations.

Deployment configuration updated.

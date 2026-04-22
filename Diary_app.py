"""
Personal Diary App — Single File
=================================
All HTML templates are embedded as Python strings (no /templates folder needed).

Run:
    pip install flask werkzeug
    python diary_all_in_one.py

Visit: http://localhost:5000
"""

import os
import sqlite3
from datetime import datetime
from functools import wraps

from flask import (Flask, g, redirect, render_template_string,
                   request, session, url_for, flash)
from werkzeug.security import check_password_hash, generate_password_hash

# ── App Setup ────────────────────────────────────────────────────────────────

app = Flask(__name__, template_folder=None)
app.secret_key = "diary-secret-key-change-me"
DATABASE = os.path.join(os.path.dirname(__file__), "diary.db")

# ══════════════════════════════════════════════════════════════════════════════
#  TEMPLATES  (embedded as Python strings)
# ══════════════════════════════════════════════════════════════════════════════

_CSS = """
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --bg: #0d0b08; --surface: #141210; --card: #1a1714; --border: #2e2a24;
  --accent: #c9a96e; --accent-dim: #8b7148;
  --text: #e8e0d4; --text-muted: #7a7060; --text-soft: #b0a898;
  --danger: #b05a5a; --radius: 4px;
}

html { font-size: 16px; }

body {
  font-family: 'Cormorant Garamond', Georgia, serif;
  background: var(--bg); color: var(--text); min-height: 100vh;
  background-image:
    radial-gradient(ellipse 80% 60% at 50% -10%, rgba(201,169,110,0.07) 0%, transparent 70%),
    repeating-linear-gradient(0deg, transparent, transparent 39px,
      rgba(46,42,36,0.3) 39px, rgba(46,42,36,0.3) 40px);
}

/* NAV */
nav {
  position: sticky; top: 0; z-index: 100;
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 2rem; height: 56px;
  background: rgba(13,11,8,0.92); backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border);
}
.nav-brand {
  font-size: 1.25rem; font-weight: 600; letter-spacing: 0.12em;
  color: var(--accent); text-decoration: none; text-transform: uppercase;
}
.nav-brand em { font-style: italic; font-weight: 300; color: var(--text-soft); }
.nav-links { display: flex; align-items: center; gap: 1.5rem; }
.nav-links a {
  font-family: 'DM Mono', monospace; font-size: 0.72rem;
  letter-spacing: 0.1em; text-transform: uppercase;
  color: var(--text-muted); text-decoration: none; transition: color .2s;
}
.nav-links a:hover { color: var(--accent); }
.nav-user {
  font-family: 'DM Mono', monospace; font-size: 0.7rem;
  color: var(--accent-dim); letter-spacing: 0.08em;
}

/* MAIN */
main { max-width: 820px; margin: 0 auto; padding: 3rem 1.5rem 5rem; }

/* FLASH */
.flashes { list-style: none; margin-bottom: 1.5rem; }
.flashes li {
  padding: .65rem 1rem; border-radius: var(--radius);
  font-family: 'DM Mono', monospace; font-size: .78rem;
  background: rgba(176,90,90,0.12); border: 1px solid rgba(176,90,90,0.35);
  color: #d48585;
}

/* PAGE HEADER */
.page-header {
  display: flex; align-items: flex-end; justify-content: space-between;
  margin-bottom: 2.5rem; padding-bottom: 1.2rem;
  border-bottom: 1px solid var(--border);
}
.page-header h1 { font-size: 2.4rem; font-weight: 300; letter-spacing: 0.02em; line-height: 1; }
.page-header h1 em { color: var(--accent); }

/* BUTTONS */
.btn {
  display: inline-flex; align-items: center; gap: .4rem;
  padding: .55rem 1.2rem; font-family: 'DM Mono', monospace; font-size: .75rem;
  letter-spacing: .08em; text-transform: uppercase;
  border-radius: var(--radius); text-decoration: none;
  cursor: pointer; transition: all .2s; border: 1px solid;
}
.btn-primary { background: var(--accent); color: #0d0b08; border-color: var(--accent); }
.btn-primary:hover { background: #debb85; border-color: #debb85; }
.btn-ghost { background: transparent; color: var(--text-soft); border-color: var(--border); }
.btn-ghost:hover { border-color: var(--accent); color: var(--accent); }
.btn-danger { background: transparent; color: var(--danger); border-color: rgba(176,90,90,0.4); }
.btn-danger:hover { background: rgba(176,90,90,0.1); }

/* CARDS */
.card {
  background: var(--card); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 1.6rem 1.8rem;
  position: relative; transition: border-color .2s, transform .15s;
}
.card::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
  background: linear-gradient(90deg, transparent, var(--accent), transparent);
  opacity: 0; transition: opacity .2s;
}
.card:hover::before { opacity: 1; }

/* FORMS */
.form-group { margin-bottom: 1.4rem; }
label {
  display: block; margin-bottom: .45rem;
  font-family: 'DM Mono', monospace; font-size: .72rem;
  letter-spacing: .1em; text-transform: uppercase; color: var(--accent-dim);
}
input[type=text], input[type=password], textarea {
  width: 100%; padding: .7rem .9rem;
  background: var(--surface); color: var(--text);
  border: 1px solid var(--border); border-radius: var(--radius);
  font-family: 'Cormorant Garamond', serif; font-size: 1.05rem;
  outline: none; transition: border-color .2s;
}
input[type=text]:focus, input[type=password]:focus, textarea:focus { border-color: var(--accent); }
textarea { resize: vertical; min-height: 280px; line-height: 1.75; }
input::placeholder, textarea::placeholder { color: var(--text-muted); }

/* ENTRY LIST */
.entry-list { display: flex; flex-direction: column; gap: 1rem; }
.entry-card { display: block; text-decoration: none; color: inherit; }
.entry-card .card { cursor: pointer; }
.entry-card .card:hover { border-color: var(--accent-dim); transform: translateX(3px); }
.entry-meta { display: flex; align-items: center; gap: 1rem; margin-bottom: .5rem; }
.entry-date { font-family: 'DM Mono', monospace; font-size: .68rem; color: var(--accent-dim); letter-spacing: .06em; }
.entry-title { font-size: 1.3rem; font-weight: 400; margin-bottom: .4rem; }
.entry-preview {
  color: var(--text-muted); font-size: .95rem; font-style: italic; line-height: 1.55;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}
.entry-count { font-family: 'DM Mono', monospace; font-size: .7rem; color: var(--text-muted); letter-spacing: .06em; }

/* EMPTY STATE */
.empty { text-align: center; padding: 5rem 2rem; color: var(--text-muted); }
.empty .icon { font-size: 3rem; margin-bottom: 1rem; opacity: .4; }
.empty p { font-size: 1.1rem; font-style: italic; margin-bottom: 1.5rem; }

/* ENTRY VIEW */
.entry-body { font-size: 1.15rem; line-height: 1.9; color: var(--text-soft); white-space: pre-wrap; }
.entry-full-title { font-size: 2rem; font-weight: 300; margin-bottom: .4rem; }
.divider { border: none; border-top: 1px solid var(--border); margin: 1.5rem 0; }

/* AUTH */
.auth-wrap { display: flex; align-items: center; justify-content: center; min-height: calc(100vh - 56px); }
.auth-box {
  width: 100%; max-width: 420px; background: var(--card);
  border: 1px solid var(--border); border-radius: 6px;
  padding: 2.5rem 2.2rem; position: relative; overflow: hidden;
}
.auth-box::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
  background: linear-gradient(90deg, var(--accent-dim), var(--accent), var(--accent-dim));
}
.auth-title { font-size: 1.8rem; font-weight: 300; margin-bottom: .3rem; }
.auth-title em { color: var(--accent); }
.auth-sub { font-family: 'DM Mono', monospace; font-size: .72rem; color: var(--text-muted); letter-spacing: .08em; margin-bottom: 2rem; }
.auth-footer { margin-top: 1.2rem; font-family: 'DM Mono', monospace; font-size: .72rem; color: var(--text-muted); text-align: center; }
.auth-footer a { color: var(--accent-dim); text-decoration: none; }
.auth-footer a:hover { color: var(--accent); }

@media (max-width: 600px) {
  nav { padding: 0 1rem; }
  main { padding: 2rem 1rem 4rem; }
  .page-header h1 { font-size: 1.8rem; }
}
"""

_BASE_HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>{{ page_title }}</title>
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300;1,400&family=DM+Mono:wght@300;400&display=swap" rel="stylesheet"/>
  <style>""" + _CSS + """</style>
</head>
<body>
  {% if session.user_id %}
  <nav>
    <a href="{{ url_for('index') }}" class="nav-brand">My <em>Diary</em></a>
    <div class="nav-links">
      <span class="nav-user">{{ session.username }}</span>
      <a href="{{ url_for('new_entry') }}">+ New</a>
      <a href="{{ url_for('logout') }}">Logout</a>
    </div>
  </nav>
  {% endif %}
  <main>
    {% with messages = get_flashed_messages() %}
      {% if messages %}
        <ul class="flashes">{% for m in messages %}<li>{{ m }}</li>{% endfor %}</ul>
      {% endif %}
    {% endwith %}
"""

_BASE_FOOT = """  </main>
</body>
</html>"""

# ── Individual page templates ─────────────────────────────────────────────────

TMPL_LOGIN = _BASE_HEAD + """
<div class="auth-wrap">
  <div class="auth-box">
    <h1 class="auth-title">Welcome <em>back</em></h1>
    <p class="auth-sub">Sign in to your private journal</p>
    <form method="POST" action="{{ url_for('login') }}">
      <div class="form-group">
        <label for="username">Username</label>
        <input type="text" id="username" name="username" placeholder="your username"
               required autocomplete="username"/>
      </div>
      <div class="form-group">
        <label for="password">Password</label>
        <input type="password" id="password" name="password" placeholder="••••••••"
               required autocomplete="current-password"/>
      </div>
      <button type="submit" class="btn btn-primary"
              style="width:100%;justify-content:center;padding:.75rem;">
        Enter Journal
      </button>
    </form>
    <p class="auth-footer">
      No account? <a href="{{ url_for('register') }}">Create one</a>
    </p>
  </div>
</div>
""" + _BASE_FOOT

TMPL_REGISTER = _BASE_HEAD + """
<div class="auth-wrap">
  <div class="auth-box">
    <h1 class="auth-title">Create <em>account</em></h1>
    <p class="auth-sub">Begin your private journaling space</p>
    <form method="POST" action="{{ url_for('register') }}">
      <div class="form-group">
        <label for="username">Username</label>
        <input type="text" id="username" name="username" placeholder="choose a username"
               required autocomplete="username"/>
      </div>
      <div class="form-group">
        <label for="password">Password</label>
        <input type="password" id="password" name="password" placeholder="min 6 characters"
               required autocomplete="new-password"/>
      </div>
      <div class="form-group">
        <label for="confirm">Confirm Password</label>
        <input type="password" id="confirm" name="confirm" placeholder="repeat password"
               required autocomplete="new-password"/>
      </div>
      <button type="submit" class="btn btn-primary"
              style="width:100%;justify-content:center;padding:.75rem;">
        Create Journal
      </button>
    </form>
    <p class="auth-footer">
      Already have an account? <a href="{{ url_for('login') }}">Sign in</a>
    </p>
  </div>
</div>
""" + _BASE_FOOT

TMPL_INDEX = _BASE_HEAD + """
<div class="page-header">
  <div>
    <h1>My <em>Journal</em></h1>
    <p class="entry-count" style="margin-top:.5rem;">
      {{ entries|length }} entr{{ 'y' if entries|length == 1 else 'ies' }}
    </p>
  </div>
  <a href="{{ url_for('new_entry') }}" class="btn btn-primary">+ New Entry</a>
</div>

{% if entries %}
<div class="entry-list">
  {% for e in entries %}
  <a href="{{ url_for('view_entry', entry_id=e['id']) }}" class="entry-card">
    <div class="card">
      <div class="entry-meta">
        <span class="entry-date">{{ e['created_at'][:16] }}</span>
      </div>
      <div class="entry-title">{{ e['title'] }}</div>
      <div class="entry-preview">{{ e['content'] }}</div>
    </div>
  </a>
  {% endfor %}
</div>
{% else %}
<div class="empty">
  <div class="icon">✦</div>
  <p>Your journal is empty. Begin writing.</p>
  <a href="{{ url_for('new_entry') }}" class="btn btn-primary">Write First Entry</a>
</div>
{% endif %}
""" + _BASE_FOOT

TMPL_NEW_ENTRY = _BASE_HEAD + """
<div class="page-header">
  <h1>New <em>Entry</em></h1>
  <a href="{{ url_for('index') }}" class="btn btn-ghost">← Back</a>
</div>
<div class="card">
  <form method="POST" action="{{ url_for('new_entry') }}">
    <div class="form-group">
      <label for="title">Title</label>
      <input type="text" id="title" name="title"
             placeholder="Give this moment a name…" required
             value="{{ prefill_title }}"/>
    </div>
    <div class="form-group">
      <label for="content">Entry</label>
      <textarea id="content" name="content"
                placeholder="Write freely. This is yours alone…"
                required>{{ prefill_content }}</textarea>
    </div>
    <div style="display:flex;gap:.8rem;justify-content:flex-end;margin-top:.5rem;">
      <a href="{{ url_for('index') }}" class="btn btn-ghost">Cancel</a>
      <button type="submit" class="btn btn-primary">Save Entry</button>
    </div>
  </form>
</div>
""" + _BASE_FOOT

TMPL_VIEW_ENTRY = _BASE_HEAD + """
<div class="page-header">
  <a href="{{ url_for('index') }}" class="btn btn-ghost">← All Entries</a>
  <form method="POST"
        action="{{ url_for('delete_entry', entry_id=entry['id']) }}"
        onsubmit="return confirm('Delete this entry permanently?')">
    <button type="submit" class="btn btn-danger">Delete</button>
  </form>
</div>
<div class="card">
  <div class="entry-date" style="margin-bottom:.8rem;">{{ entry['created_at'] }}</div>
  <h2 class="entry-full-title">{{ entry['title'] }}</h2>
  <hr class="divider"/>
  <div class="entry-body">{{ entry['content'] }}</div>
</div>
""" + _BASE_FOOT


# ══════════════════════════════════════════════════════════════════════════════
#  DATABASE
# ══════════════════════════════════════════════════════════════════════════════

def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


def init_db():
    with app.app_context():
        db = get_db()
        db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                username   TEXT UNIQUE NOT NULL,
                password   TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS entries (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER NOT NULL,
                title      TEXT NOT NULL,
                content    TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
        """)
        db.commit()


# ══════════════════════════════════════════════════════════════════════════════
#  AUTH HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def render(template_str, **ctx):
    """Thin wrapper: always injects page_title default."""
    ctx.setdefault("page_title", "My Diary")
    return render_template_string(template_str, **ctx)


# ══════════════════════════════════════════════════════════════════════════════
#  ROUTES
# ══════════════════════════════════════════════════════════════════════════════

# ── Home ──────────────────────────────────────────────────────────────────────
@app.route("/")
@login_required
def index():
    db = get_db()
    entries = db.execute(
        "SELECT * FROM entries WHERE user_id = ? ORDER BY created_at DESC",
        (session["user_id"],),
    ).fetchall()
    return render(TMPL_INDEX, page_title="Journal — My Diary", entries=entries)


# ── Login ─────────────────────────────────────────────────────────────────────
@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("index"))
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("index"))
        flash("Invalid username or password.")
    return render(TMPL_LOGIN, page_title="Login — My Diary")


# ── Register ──────────────────────────────────────────────────────────────────
@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("index"))
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        confirm  = request.form["confirm"]
        if not username or not password:
            flash("All fields are required.")
        elif password != confirm:
            flash("Passwords do not match.")
        elif len(password) < 6:
            flash("Password must be at least 6 characters.")
        else:
            db = get_db()
            if db.execute(
                "SELECT id FROM users WHERE username = ?", (username,)
            ).fetchone():
                flash("Username already taken.")
            else:
                db.execute(
                    "INSERT INTO users (username, password) VALUES (?, ?)",
                    (username, generate_password_hash(password)),
                )
                db.commit()
                flash("Account created! Please log in.")
                return redirect(url_for("login"))
    return render(TMPL_REGISTER, page_title="Register — My Diary")


# ── Logout ────────────────────────────────────────────────────────────────────
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ── New Entry ─────────────────────────────────────────────────────────────────
@app.route("/new", methods=["GET", "POST"])
@login_required
def new_entry():
    if request.method == "POST":
        title   = request.form["title"].strip()
        content = request.form["content"].strip()
        if not title or not content:
            flash("Both title and content are required.")
        else:
            db  = get_db()
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            db.execute(
                "INSERT INTO entries (user_id, title, content, created_at) VALUES (?, ?, ?, ?)",
                (session["user_id"], title, content, now),
            )
            db.commit()
            return redirect(url_for("index"))
    return render(
        TMPL_NEW_ENTRY,
        page_title="New Entry — My Diary",
        prefill_title=request.form.get("title", ""),
        prefill_content=request.form.get("content", ""),
    )


# ── View Entry ────────────────────────────────────────────────────────────────
@app.route("/entry/<int:entry_id>")
@login_required
def view_entry(entry_id):
    db    = get_db()
    entry = db.execute(
        "SELECT * FROM entries WHERE id = ? AND user_id = ?",
        (entry_id, session["user_id"]),
    ).fetchone()
    if not entry:
        return redirect(url_for("index"))
    return render(TMPL_VIEW_ENTRY, page_title=entry["title"] + " — My Diary", entry=entry)


# ── Delete Entry ──────────────────────────────────────────────────────────────
@app.route("/entry/<int:entry_id>/delete", methods=["POST"])
@login_required
def delete_entry(entry_id):
    db = get_db()
    db.execute(
        "DELETE FROM entries WHERE id = ? AND user_id = ?",
        (entry_id, session["user_id"]),
    )
    db.commit()
    return redirect(url_for("index"))


# ══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    init_db()
    print("\n  Personal Diary App")
    print("  ─────────────────────────────────")
    print("  Visit → http://localhost:5000")
    print("  Register a new account to get started.\n")
    app.run(debug=True, port=5000)

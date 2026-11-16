# Personal Expense Tracker

A student-focused expense tracker built with **Python (Flask) + SQLite**, designed around
**object-oriented programming**, with **machine learning** (auto-categorization) and
**rule-based AI** (budget recommendations).

## Run it

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run.py                    # open http://127.0.0.1:5000
python -m pytest                 # run the tests
```

Set `SECRET_KEY` in your environment so sessions survive restarts.

## Project structure

```
expense_tracker/
├── run.py                     # starts the app
├── requirements.txt
├── app/
│   ├── __init__.py            # create_app(): wires Database -> Repositories -> Services
│   ├── exceptions.py          # ValidationError, AuthError
│   ├── security.py            # login_required, CSRF protection
│   ├── models/                # OOP core
│   │   ├── transaction.py     # Transaction (abstract), Income, Expense, TransactionFactory
│   │   ├── user.py            # User (hashed password, validated budget)
│   │   └── categories.py
│   ├── database/              # data layer
│   │   ├── db.py              # Database wrapper
│   │   ├── repositories.py    # BaseRepository (abstract), UserRepository, TransactionRepository
│   │   └── schema.sql
│   ├── services/              # business logic
│   │   ├── auth_service.py
│   │   └── tracker_service.py
│   ├── ai/
│   │   ├── categorizer.py     # ML: TF-IDF + Naive Bayes expense classifier
│   │   ├── recommender.py     # BudgetRecommender (abstract) + rule-based + forecast
│   │   └── data/sample_expenses.csv   # training data (add more rows to improve it)
│   ├── routes/                # Flask blueprints (auth.py, main.py)
│   ├── templates/             # HTML (Jinja2)
│   └── static/style.css
└── tests/                     # pytest: models, repositories, AI, web app
```

## OOP concepts (where to point during defense)

| Concept | Where | Example |
|---|---|---|
| **Abstraction** | `Transaction`, `BudgetRecommender`, `BaseRepository` | Abstract classes cannot be instantiated; they define required methods (`signed_amount`, `recommend`, `table`) |
| **Inheritance** | `Income`, `Expense` extend `Transaction`; repositories extend `BaseRepository` | Shared fields, validation and `apply_to_balance()` are inherited |
| **Polymorphism** | `signed_amount()`, `describe()`, `allowed_categories()`, `recommend()` | The balance loop calls `tx.apply_to_balance()` without caring if it is income or expense |
| **Encapsulation** | Private `_amount`, `_password_hash`, validated property setters | `tx.amount = -5` raises `ValidationError`; the password hash is never exposed directly |
| Composition / patterns | `CompositeRecommender`, `TransactionFactory`, repository pattern | Services are given their dependencies (dependency injection) |

## AI vs ML (important for the panel)

- **ML:** `ExpenseCategorizer` learns from labeled examples (TF-IDF + Multinomial Naive Bayes, scikit-learn).
- **AI, not ML:** `RuleBasedRecommender` and `ForecastRecommender` use fixed rules and a simple projection; they do not learn.
- The recommender interface is abstract, so a trained model can be added later as another subclass.

## Security checklist

- Passwords hashed (Werkzeug/PBKDF2), never stored in plain text
- Parameterized SQL everywhere (no SQL injection)
- Every transaction query filtered by `user_id` (users only see their own data)
- Server-side input validation in the models; Jinja2 auto-escapes output (XSS)
- CSRF token on every POST; HttpOnly + SameSite session cookie; 30-minute session timeout
- Session reset on login; same error message for wrong username or password
- No bank or card numbers stored (data minimization)

**Not yet done (say this honestly):** HTTPS (needed on deployment), login rate limiting,
two-factor auth, encryption at rest, audit logging.

## Ideas for next steps

1. Add more rows to `sample_expenses.csv` (or let users correct a category and retrain).
2. Charts on the dashboard (monthly trend, category pie).
3. Recurring transactions (allowance every week).
4. A third recommender that uses a trained regression model for spending forecasts.

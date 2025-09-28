from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from datetime import date, datetime
import os

app = Flask(__name__)

# --- SQLite DB in project folder ---
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(BASE_DIR, "expenses.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# --- Model ---
class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(120), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    note = db.Column(db.String(255), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "category": self.category,
            "amount": self.amount,
            "date": self.date.strftime("%Y-%m-%d"),
            "note": self.note or ""
        }

# --- Create DB tables once ---
with app.app_context():
    db.create_all()

# --- Pages ---
@app.route("/")
def index():
    return render_template("index.html")

# --- APIs ---
@app.route("/api/expenses", methods=["GET"])
def api_get_expenses():
    category = request.args.get("category", type=str)
    q = request.args.get("q", type=str)
    from_str = request.args.get("from", type=str)
    to_str = request.args.get("to", type=str)

    query = Expense.query
    if category:
        query = query.filter(Expense.category == category)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(Expense.category.ilike(like), Expense.note.ilike(like)))
    if from_str:
        try:
            df = datetime.strptime(from_str, "%Y-%m-%d").date()
            query = query.filter(Expense.date >= df)
        except ValueError:
            pass
    if to_str:
        try:
            dt = datetime.strptime(to_str, "%Y-%m-%d").date()
            query = query.filter(Expense.date <= dt)
        except ValueError:
            pass

    items = query.order_by(Expense.date.desc(), Expense.id.desc()).all()
    return jsonify([e.to_dict() for e in items])

@app.route("/api/expenses", methods=["POST"])
def api_add_expense():
    data = request.get_json(force=True)
    category = (data.get("category") or "").strip()
    amount = float(data.get("amount") or 0)
    date_str = (data.get("date") or "").strip()
    note = (data.get("note") or "").strip()

    if not category:
        return jsonify({"error": "Category is required"}), 400
    if amount <= 0:
        return jsonify({"error": "Amount must be greater than 0"}), 400

    try:
        dval = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else date.today()
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

    exp = Expense(category=category, amount=amount, date=dval, note=note)
    db.session.add(exp)
    db.session.commit()
    return jsonify(exp.to_dict()), 201

@app.route("/api/expenses/<int:expense_id>", methods=["PUT"])
def api_update_expense(expense_id):
    exp = Expense.query.get_or_404(expense_id)
    data = request.get_json(force=True)

    if "category" in data:
        exp.category = (data.get("category") or exp.category).strip()
    if "amount" in data:
        amt = float(data.get("amount") or exp.amount)
        if amt <= 0:
            return jsonify({"error": "Amount must be greater than 0"}), 400
        exp.amount = amt
    if "date" in data:
        ds = (data.get("date") or "").strip()
        if ds:
            try:
                exp.date = datetime.strptime(ds, "%Y-%m-%d").date()
            except ValueError:
                return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
    if "note" in data:
        exp.note = (data.get("note") or "").strip()

    db.session.commit()
    return jsonify(exp.to_dict())

@app.route("/api/expenses/<int:expense_id>", methods=["DELETE"])
def api_delete_expense(expense_id):
    exp = Expense.query.get_or_404(expense_id)
    db.session.delete(exp)
    db.session.commit()
    return jsonify({"status": "deleted", "id": expense_id})

@app.route("/api/summary", methods=["GET"])
def api_summary():
    rows = Expense.query.all()
    total = sum(e.amount for e in rows)
    by_cat = {}
    for e in rows:
        by_cat[e.category] = by_cat.get(e.category, 0) + e.amount
    return jsonify({"total": total, "byCategory": by_cat})

if __name__ == "__main__":
    app.run(debug=True)


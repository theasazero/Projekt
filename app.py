from flask import Flask, render_template, request, redirect, session
from openai import OpenAI
import stripe
import os

app = Flask(__name__)
app.secret_key = "mein_geheimer_key_123"

# Keys sicher aus Environment Variables laden
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
app.secret_key = os.getenv("SECRET_KEY", "dev-secret")
BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:5000")


@app.route("/", methods=["GET", "POST"])
def index():
    if "usage" not in session:
        session["usage"] = 0

    result = None

    if request.method == "POST":
        if session["usage"] >= 2:
            return redirect("/pricing")

        name = request.form.get("name", "").strip()
        job = request.form.get("job", "").strip()
        branch = request.form.get("branch", "").strip()
        tone = request.form.get("tone", "").strip()
        experience = request.form.get("experience", "").strip()
        strengths = request.form.get("strengths", "").strip()

        prompt = f"""
Du bist ein professioneller Karriereberater und Bewerbungsexperte.

Erstelle ein überzeugendes, modernes und individuelles Bewerbungsschreiben auf Deutsch.

Daten der Person:
- Name: {name}
- Gewünschter Job: {job}
- Branche: {branch}
- Tonalität: {tone}
- Berufserfahrung: {experience}
- Besondere Stärken / Erfolge: {strengths}

Wichtige Anforderungen:
- Schreibe professionell, klar und überzeugend
- Nutze eine natürliche, moderne Sprache
- Keine billigen Standardfloskeln
- Das Schreiben soll individuell wirken
- Gute Struktur mit Einleitung, Hauptteil und Schluss
- Hebe Motivation, relevante Erfahrung und Stärken hervor
- Maximal ca. 350 Wörter
- Gib nur das fertige Bewerbungsschreiben aus, keine Erklärungen davor oder danach
"""

        try:
            response = openai_client.responses.create(
                model="gpt-4.1-mini",
                input=prompt
            )
            result = response.output_text
            session["usage"] += 1

        except Exception as e:
            result = f"Fehler: {e}"

    return render_template("index.html", result=result)


@app.route("/pricing")
def pricing():
    return render_template("pricing.html")


@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    try:
        checkout_session = stripe.checkout.Session.create(
            mode="payment",
            line_items=[
                {
                    "price_data": {
                        "currency": "eur",
                        "product_data": {
                            "name": "JobBoost AI Premium",
                            "description": "Premium-Zugang für dein Bewerbungstool"
                        },
                        "unit_amount": 499
                    },
                    "quantity": 1
                }
            ],
            success_url=BASE_URL + "/success?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=BASE_URL + "/cancel"
        )

        return redirect(checkout_session.url, code=303)

    except Exception as e:
        return f"Stripe Fehler: {e}"


@app.route("/success")
def success():
    session_id = request.args.get("session_id")
    return render_template("success.html", session_id=session_id)


@app.route("/cancel")
def cancel():
    return render_template("cancel.html")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
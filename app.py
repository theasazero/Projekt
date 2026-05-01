from flask import Flask, render_template, request, redirect, session, send_file
from openai import OpenAI
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import stripe
import os
import io

app = Flask(__name__)
app.secret_key = os.getenv("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", "dev-secret-change-me")

OPENAI_API_KEY = os.getenv("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")
stripe.api_key = os.getenv("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")
BASE_URL = os.getenv("BASE_URL", "https://projekt-imje.onrender.com")

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
Du bist ein professioneller Karriereberater.

Erstelle ein modernes Bewerbungsschreiben auf Deutsch.

Name: {name}
Job: {job}
Branche: {branch}
Tonalität: {tone}
Erfahrung: {experience}
Stärken: {strengths}

Anforderungen:
- Klar, professionell und überzeugend schreiben
- Keine billigen Standardfloskeln
- Gute Struktur mit Einleitung, Hauptteil und Schluss
- Maximal 300 bis 350 Wörter
- Gib nur das fertige Bewerbungsschreiben aus
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
    if not STRIPE_SECRET_KEY:
        return "Stripe Fehler: STRIPE_SECRET_KEY fehlt.", 500

    try:
        checkout_session = stripe.checkout.Session.create(
            mode="payment",
            line_items=[
                {
                    "price_data": {
                        "currency": "eur",
                        "product_data": {
                            "name": "JobBoost AI Premium",
                            "description": "Premium-Zugang für unbegrenzte Bewerbungen"
                        },
                        "unit_amount": 499
                    },
                    "quantity": 1
                }
            ],
            success_url=BASE_URL + "/success",
            cancel_url=BASE_URL + "/cancel"
        )

        return redirect(checkout_session.url, code=303)

    except Exception as e:
        return f"Stripe Fehler: {e}", 500


@app.route("/download-pdf", methods=["POST"])
def download_pdf():
    text = request.form.get("text", "").strip()

    if not text:
        return redirect("/")

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()
    normal_style = styles["Normal"]
    title_style = styles["Title"]

    story = [
        Paragraph("Bewerbungsschreiben", title_style),
        Spacer(1, 18)
    ]

    for line in text.split("\n"):
        clean_line = line.strip()
        if clean_line:
            story.append(Paragraph(clean_line, normal_style))
            story.append(Spacer(1, 10))

    doc.build(story)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="bewerbung.pdf",
        mimetype="application/pdf"
    )


@app.route("/success")
def success():
    session.clear()
    return render_template("success.html")


@app.route("/cancel")
def cancel():
    return render_template("cancel.html")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
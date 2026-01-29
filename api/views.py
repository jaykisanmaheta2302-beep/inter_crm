from rest_framework.decorators import api_view
from rest_framework.response import Response
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
import json
import os
import csv
from pathlib import Path
CSV_FILE = Path("eval_results.csv")
load_dotenv()
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",    
    api_key= "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"
)
def save_to_csv(row):
    file_exists = CSV_FILE.exists()
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "id",
                "raw_text",
                "full_name",
                "phone",
                "address",
                "city",
                "locality",
                "summary",
                "created_at",
                "hitl_status",
            ],
        )

        if not file_exists:
            writer.writeheader()

        writer.writerow(row)


@api_view(["GET"])
def dashboard_results(request):
    """Return all saved CRM extraction results from the CSV file."""
    if not CSV_FILE.exists():
        return Response([])

    with open(CSV_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return Response(list(reader))


@api_view(["POST"])
def voice_to_json(request):
    """Convert a transcript into structured CRM JSON format."""
    transcript = request.data.get("transcript")

    if not transcript:
        return Response(
            {"error": "The 'transcript' field is required."},
            status=400
        )

    prompt = f"""
You are a CRM information extraction system.

Extract structured CRM data from the text below.

Rules:
- Return ONLY valid JSON
- Do NOT include explanations
- If a field is missing, set it to null

Schema:
{{
  "customer": {{
    "full_name": null,
    "phone": null,
    "address": null,
    "city": null,
    "locality": null
  }},
  "interaction": {{
    "summary": null,
    "created_at": null
  }}
}}

Text:
\"\"\"{transcript}\"\"\"
"""

    try:
        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            max_tokens=365,
            temperature=0,
            messages=[
                {"role": "user", "content": prompt}
            ],
            extra_headers={
                "HTTP-Referer": "http://localhost",
                "X-Title": "VoiceCRM",
            },
        )

        content = response.choices[0].message.content
        structured_json = json.loads(content)

    except Exception as e:
        structured_json = {
            "customer": {
                "full_name": None,
                "phone": None,
                "address": None,
                "city": None,
                "locality": None
            },
            "interaction": {
                "summary": transcript,
                "created_at": None
            },
            "error": str(e)
        }

    save_to_csv({
        "id": datetime.utcnow().timestamp(),
        "raw_text": transcript,
        "full_name": structured_json["customer"]["full_name"],
        "phone": structured_json["customer"]["phone"],
        "address": structured_json["customer"]["address"],
        "city": structured_json["customer"]["city"],
        "locality": structured_json["customer"]["locality"],
        "summary": structured_json["interaction"]["summary"],
        "created_at": datetime.utcnow().isoformat(),
        "hitl_status": "PENDING",
    })

    return Response({
        "status": "success",
        "message": "Transcript successfully processed into structured CRM data.",
        "raw_text": transcript,
        "structured_json": structured_json,
        "created_at": datetime.utcnow().isoformat()
    })

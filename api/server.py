import os
from pathlib import Path
from fastapi import FastAPI, Depends
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi_clerk_auth import ClerkConfig, ClerkHTTPBearer, HTTPAuthorizationCredentials
from openai import AzureOpenAI
from typing import Iterator

app = FastAPI()

# Add CORS middleware (allows frontend to call backend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Clerk authentication setup
clerk_config = ClerkConfig(jwks_url=os.getenv("CLERK_JWKS_URL"))
clerk_guard = ClerkHTTPBearer(clerk_config)

AZURE_OPENAI_ENDPOINT    = os.getenv("AZURE_OPENAI_ENDPOINT")    #"https://<resource>.openai.azure.com/"
AZURE_OPENAI_API_KEY     = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION") # ex:"2024-12-01-preview"
AZURE_OPENAI_DEPLOYMENT  = os.getenv("AZURE_OPENAI_DEPLOYMENT")  # ex:"gpt-5-nano"


class Visit(BaseModel):
    patient_name: str
    date_of_visit: str
    notes: str

system_prompt = """
You are provided with clinical notes from a doctor documenting a patient's visit.
Your job is to generate a structured, clinically useful summary for the doctor and draft a clear, patient-friendly email for follow-up.
Respond with these three sections, using exactly the specified headings:

### Summary of Visit for the Doctor's Records
Include: patient’s initials (or a safe identifier), age, and date of visit. Summarize the main complaints, history (medical, surgical, social), examination findings, diagnoses or issues addressed, treatments or procedures performed, medication changes, results reviewed, and notable discussion points (including informed consent or preferences). Flag important safety information or clinical “red flags.” Use bullet points for clarity. Note any references to relevant attachments or linked external documents.

### Next Steps for the Doctor
List specific actions including pending tests, referrals, medication adjustments, monitoring/support instructions, and reminders (e.g. review labs, arrange specialist consult). Clearly state the timing for follow-up and any red-flag alerts requiring urgent attention. Include care coordination (e.g., communication between providers) and, if applicable, instructions relevant to remote or telehealth consultations.

### Draft of Email to Patient in Patient-Friendly Language
Summarize the visit in clear, easy-to-understand language with date and provider details. Explain findings, diagnoses, what they mean, and next steps with timelines (e.g., when to book follow-up, what to do if symptoms worsen). Include actionable instructions, warning signs, and how to reach out for help or clarification. Make the language accessible for all literacy levels and encourage questions. Mention if translation or accessibility support is available. Do not include unnecessary sensitive information.

**Additional requirements:**
- Avoid copying verbatim from original notes in any section.
- Respect privacy and clinical compliance (use minimal identifiers only as needed).
- Tailor all content contextually to the provided notes and the specifics of the visit.
- Note at the end if attachments or external reports are referenced or available.
"""


def user_prompt_for(visit: Visit) -> str:
    return f"""Create the summary, next steps and draft email for:
Patient Name: {visit.patient_name}
Date of Visit: {visit.date_of_visit}
Notes:
{visit.notes}"""

@app.post("/api/consultation")
def consultation_summary(
    visit: Visit,
    creds: HTTPAuthorizationCredentials = Depends(clerk_guard),
):
    user_id = creds.decoded["sub"]
    if not AZURE_OPENAI_ENDPOINT or ".openai.azure.com" not in AZURE_OPENAI_ENDPOINT:        
        return JSONResponse({"error": "Invalid AZURE_OPENAI_ENDPOINT (expected https://<resource>.openai.azure.com)"}, status_code=400)
    if not AZURE_OPENAI_API_KEY:
        return JSONResponse({"error": "AZURE_OPENAI_API_KEY not set"}, status_code=400)
    if not AZURE_OPENAI_DEPLOYMENT:
        return JSONResponse({"error": "AZURE_OPENAI_DEPLOYMENT not set (must be Azure deployment name)"}, status_code=400)
    if not AZURE_OPENAI_API_VERSION:
         return JSONResponse({"error": "AZURE_OPENAI_API_VERSION not set)"}, status_code=400)


    client = AzureOpenAI(
        api_version=AZURE_OPENAI_API_VERSION,
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_API_KEY,
    )
    
    user_prompt = user_prompt_for(visit)

    prompt = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    
    def sse() -> Iterator[str]:
        # Initial comment confirms the stream opened (SSE)
        yield ": stream-open\n\n"
        try:
            stream = client.chat.completions.create(
                model=AZURE_OPENAI_DEPLOYMENT,   # deployment name
                messages=prompt,
                stream=True,
                # Optional knobs to keep it tight and consistent
                max_completion_tokens=5000,  # adjust to taste (ensures brevity)
            )

            #last_keepalive = time.time()
            for chunk in stream:
                text = None
                try:
                    delta = chunk.choices[0].delta
                    text = delta.get("content") if isinstance(delta, dict) else getattr(delta, "content", None)
                except Exception:
                    text = None

                if text:
                    lines = text.split("\n")
                    for line in lines[:-1]:
                        yield f"data: {line}\n\n"
                        yield "data:  \n"
                    yield f"data: {lines[-1]}\n\n"

            # End-of-stream signal (helps client stop cleanly)
           # yield "event: done\ndata: [DONE]\n\n"

        except Exception as e:
            yield f"event: error\ndata: {str(e)}\n\n"

    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }
    return StreamingResponse(sse(), media_type="text/event-stream", headers=headers)

@app.get("/health")
def health_check():
    """Health check endpoint for AWS App Runner"""
    return {"status": "healthy"}

# Serve static files (our Next.js export) - MUST BE LAST!
static_path = Path("static")
if static_path.exists():
    # Serve index.html for the root path
    @app.get("/")
    async def serve_root():
        return FileResponse(static_path / "index.html")
    
    # Mount static files for all other routes
    app.mount("/", StaticFiles(directory="static", html=True), name="static")
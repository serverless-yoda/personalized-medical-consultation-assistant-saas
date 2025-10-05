# PersonalMed Assistant - Personalized Medical Consultation Assistant

PersonalMed Assistant is an AI-powered medical consultation assistant designed to generate professional summaries, action items, and patient communications from your consultation notes. It helps healthcare professionals streamline patient documentation and enhance patient care with intelligent automation.

---

## Features

- Generate comprehensive and professional medical consultation summaries  
- Create clear next steps and follow-up actions for every consultation  
- Automatically draft patient-friendly email communications  
- AI-driven insights and summaries tailored to personalized patient visits  
- Easy-to-use interface optimized for healthcare professionals  
- Secure authentication and subscription management via Clerk  

---

## Getting Started

### Prerequisites

- Node.js 18+  
- npm or yarn package manager  
- Clerk account for authentication and subscription management  


### Technologies Used

- Next.js 13 (React + Server Components)  
- Clerk for authentication and subscription billing  
- React Datepicker for selecting dates  
- React Markdown for rendering generated summaries  
- OpenAI or custom AI backend for generating summaries and emails  

### Docker

- Load variables from .env file
```
Get-Content .env | ForEach-Object {
    if ($_ -match '^(.+?)=(.+)$') {
        [System.Environment]::SetEnvironmentVariable($matches[1], $matches[2])
    }
}
```
- Check variable
```
Get-ChildItem Env:
```
- Build docker
```
docker build `
  --build-arg NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY="$env:NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY" `
  -t consultation-app .

```
- Run docker
```
docker run -p 8000:8000 `
  -e CLERK_SECRET_KEY="$CLERK_SECRET_KEY" `
  -e CLERK_JWKS_URL="$CLERK_JWKS_URL" `
  -e AZURE_OPENAI_API_KEY="$AZURE_OPENAI_API_KEY" `
  -e AZURE_OPENAI_ENDPOINT="$AZURE_OPENAI_ENDPOINT" `
  -e AZURE_OPENAI_API_VERSION="$AZURE_OPENAI_API_VERSION" `
  -e AZURE_OPENAI_DEPLOYMENT="$AZURE_OPENAI_DEPLOYMENT" `
  consultation-app

```
or
```
docker run -p 8000:8000 --env-file .env consultation-app
```

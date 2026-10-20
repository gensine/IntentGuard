# 🛡️ IntentGuard: Payment Intent Firewall for AI Agents

> **Hackathon:** DRUNIX Hackathon 2026 (Citi & NPCI)  
> **Theme:** India's Payments Future  
> **Category:** Fraud Prevention / Agentic Payments / Trust & Safety  

---

## 📌 Overview

**IntentGuard** is a proactive security and intent verification layer that sits between autonomous AI agents and payment rails (such as UPI / NPCI). It ensures that every payment transaction an agent attempts to execute strictly aligns with the user's explicit, cryptographically signed intent before any funds move.

---

## ⚡ Key Features

- ✍️ **Cryptographic Intent Signing (Ed25519)**: User prompts are converted into structured parameters (`max_amount`, `valid_until`, `allowed_payees`) and cryptographically signed. Any agent-side modification instantly invalidates authorization.
- 🛡️ **Two-Tier Firewall Gate**:
  - **Tier 1 (Hard Rules)**: Instant rejection for expired intents, severe budget overages, revoked permissions, or blacklisted VPAs.
  - **Tier 2 (Soft Risk Engine)**: Evaluates weighted risk scores (0.00 – 1.00) based on merchant reputation, prompt injection, and velocity loops.
- 💉 **Prompt Injection & Source Tagging**: Inspects untrusted DOM/web content to identify and block hidden prompt injection attacks (e.g., hidden comments overriding instructions).
- 🔍 **Typosquatting & Lookalike Brand Detection**: Detects fake merchants imitating trusted brands (e.g., `irctc-booking@upi` vs `irctc@upi`).
- 🛑 **Instant Emergency Kill Switch**: One-tap token revocation that freezes all agent payment capabilities immediately.
- ⛓️ **Tamper-Evident SHA-256 Audit Trail**: Append-only hash-chained ledger logging every event with mathematical verification.
- 💳 **Mock NPCI UPI Sandbox Rail**: Clears transactions and issues realistic UPI reference numbers for approved requests.

---

## 🏗️ System Architecture

```
User (Task & Budget)
        │
        ▼
Intent Service (Signs with Ed25519)
        │
        ▼ [Signed Intent]
┌──────────────────────────────────────────────┐
│             IntentGuard Firewall             │
│                                              │
│  [Hard Rules]  ──>  [Risk Engine]            │
│  • Signature check  • Lookalike detector     │
│  • Budget caps      • Injection scanner      │
│  • Expiration       • Loop guard             │
└──────────────────────┬───────────────────────┘
                       │
       ┌───────────────┼───────────────┐
       ▼               ▼               ▼
   [APPROVE]       [ASK USER]       [BLOCK]
       │               │               │
  Mock UPI Rail   One-Tap Modal   Instant Freeze
       │                               │
       └───────────────┬───────────────┘
                       ▼
         Tamper-Evident SHA-256 Audit
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.10+
- Node.js 18+ (for frontend)

### 2. Backend Setup
```bash
# Clone the repository
git clone https://github.com/gensine/intentguard.git
cd intentguard

# Create and activate virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\Activate.ps1
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt
```

### 3. Run Demo Scenarios
Run the automated test runner demonstrating all 4 hackathon judge scenarios (Normal Approve, Web Injection Attack, Borderline Ask-User, and Emergency Kill Switch):

```bash
python demo_agent/run_scenarios.py
```

### 4. Run the Firewall Server
```bash
uvicorn app.main:app --reload --port 8000 --app-dir backend
```
Interactive API docs available at: `http://127.0.0.1:8000/docs`

---

## 🧪 Verified Test Suite
Run the test suite:
```bash
python -m pytest backend/tests
```

---

## 📜 License
MIT License. Built for the Citi & NPCI DRUNIX Hackathon 2026.

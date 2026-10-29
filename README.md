# Tinolandia Proxy Wars — Geopolitical Strategy Game

An interactive, web-based geopolitical strategy game built with **Godot Engine 4 (HTML5/WebAssembly)** and a **Python (FastAPI)** game state backend powered by **Groq Llama-3.3 70B** AI commentary and **Firebase Firestore** persistence.

---

## Architecture Overview

* **Frontend UI (Godot Engine 4):** Rendered as a WebAssembly/HTML5 application using Godot's Control UI hierarchy, 2D sprite frame dice visualizer, and dynamic HTTP Client integrations.
* **Backend API (FastAPI / Uvicorn):** Manages global game state, enforces turn-order rules, executes combat mathematics, and processes automated NPC AI decision logic.
* **AI Narrative Layer (Groq API):** Uses `llama-3.3-70b-versatile` to generate contextual, real-time battle commentary based on dice roll outcomes.
* **Authentication & Database (Firebase):** Provides NoSQL state persistence (Firestore) and identity management (Firebase Auth) supporting both guest read-only view links and authenticated gameplay turns.

---

## Key Gameplay & System Rules

1. **Global Country Dataset:** Supports 200+ global nations and territories mapped to initial troop allocations based on population brackets.
2. **Troop Allocation Formula:**
   * $\le$ 5M $\rightarrow$ 1 soldier
   * $\le$ 10M $\rightarrow$ 2 soldiers
   * $\le$ 25M $\rightarrow$ 3 soldiers
   * $\le$ 50M $\rightarrow$ 4 soldiers
   * $\le$ 75M $\rightarrow$ 5 soldiers
   * $\le$ 100M $\rightarrow$ 6 soldiers
   * $\le$ 125M $\rightarrow$ 7 soldiers
   * $\le$ 150M $\rightarrow$ 8 soldiers
   * $>$ 150M $\rightarrow$ 9 soldiers
3. **Dice-Based Combat Rules:**
   * Attacking country retains at least 1 soldier in defense ($\text{Fighting Force} = \text{Attacker Troops} - 1$).
   * Dice rolls matched side-by-side ($\text{Dice Count} = \min(\text{Attacker Force}, \text{Defender Force})$).
   * Highest roll wins each die pairing; ties favor the defender.
   * Conquest occurs when defender troops drop to 0. Attacker gains conquered territory with initial garrisons calculated as $\max(2, \lfloor \text{Base Value} / 2 \rfloor)$.
4. **Automated NPC AI Logic:**
   * Evaluates relative troop advantage across controlled and enemy border nations.
   * Executes attacks when holding a numerical advantage margin ($\ge 2$ troops).
   * Generates step-by-step strategic justification text for turn logs.
   * Round 2+ Reinforcements: Adds $+2$ soldiers per owned territory to primary troop stack.
5. **Access Control:**
   * Shared links allow guest visitors read-only board access.
   * Bearer Token authentication required to trigger attack requests and execute turns.

---

## API Reference Endpoints

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | Root server health check | No |
| `GET` | `/api/countries` | Returns global 200+ country list | No |
| `GET` | `/api/game/view/{game_id}` | Read-only state view for guest shared links | No |
| `POST` | `/api/auth/signup` | Registers new user account via Firebase | No |
| `POST` | `/api/auth/login` | Authenticates user and returns Bearer token | No |
| `POST` | `/api/game/new` | Initializes 10-country session map | No |
| `POST` | `/api/game/attack` | Resolves human attack round & Groq commentary | Yes (`Bearer Token`) |
| `POST` | `/api/game/npc-turn` | Simulates single NPC strategy step & justification | No |

---

## Local Development Setup

### 1. Backend Setup

```bash
# Clone repository
git clone [https://github.com/your-username/tinolandia-proxy-wars.git](https://github.com/your-username/tinolandia-proxy-wars.git)
cd tinolandia-proxy-wars

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GROQ_API_KEY="your_groq_api_key_here"
export FIREBASE_WEB_API_KEY="your_firebase_web_api_key_here"

# Run FastAPI development server
python -m uvicorn main:app --reload --port 8000

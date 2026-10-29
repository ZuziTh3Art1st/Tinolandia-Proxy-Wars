import os
import random
import math
import requests
from typing import List, Dict, Optional
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
import firebase_admin
from firebase_admin import credentials, firestore, auth

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Groq & Firebase Setup ---
GROQ_KEY = os.environ.get("GROQ_API_KEY", "your_groq_api_key_here")
FIREBASE_WEB_API_KEY = os.environ.get("FIREBASE_WEB_API_KEY", "your_firebase_web_api_key_here")

client = Groq(api_key=GROQ_KEY)

USE_FIREBASE = False
try:
    if not firebase_admin._apps:
        if os.path.exists("serviceAccountKey.json"):
            cred = credentials.Certificate("serviceAccountKey.json")
            firebase_admin.initialize_app(cred)
            db = firestore.client()
            USE_FIREBASE = True
            print("Firebase Admin SDK initialized successfully.")
        else:
            print("serviceAccountKey.json not found. Running in local memory DB mode.")
except Exception as e:
    print(f"Firebase init error: {e}. Running in local memory DB mode.")

GAMES_DB: Dict[str, dict] = {}

# --- Global Country Dataset (~200 Nations) ---
ALL_COUNTRIES = [
    {"name": "Afghanistan", "population": 41_000_000},
    {"name": "Albania", "population": 2_750_000},
    {"name": "Algeria", "population": 45_000_000},
    {"name": "Andorra", "population": 80_000},
    {"name": "Angola", "population": 35_500_000},
    {"name": "Antigua and Barbuda", "population": 94_000},
    {"name": "Argentina", "population": 46_000_000},
    {"name": "Armenia", "population": 2_780_000},
    {"name": "Australia", "population": 26_000_000},
    {"name": "Austria", "population": 9_000_000},
    {"name": "Azerbaijan", "population": 10_100_000},
    {"name": "Bahamas", "population": 410_000},
    {"name": "Bahrain", "population": 1_500_000},
    {"name": "Bangladesh", "population": 171_000_000},
    {"name": "Barbados", "population": 281_000},
    {"name": "Belarus", "population": 9_200_000},
    {"name": "Belgium", "population": 11_600_000},
    {"name": "Belize", "population": 405_000},
    {"name": "Benin", "population": 13_300_000},
    {"name": "Bhutan", "population": 780_000},
    {"name": "Bolivia", "population": 12_200_000},
    {"name": "Bosnia and Herzegovina", "population": 3_200_000},
    {"name": "Botswana", "population": 2_600_000},
    {"name": "Brazil", "population": 215_000_000},
    {"name": "Brunei", "population": 450_000},
    {"name": "Bulgaria", "population": 6_400_000},
    {"name": "Burkina Faso", "population": 22_600_000},
    {"name": "Burundi", "population": 12_800_000},
    {"name": "Cabo Verde", "population": 590_000},
    {"name": "Cambodia", "population": 16_700_000},
    {"name": "Cameroon", "population": 27_900_000},
    {"name": "Canada", "population": 38_000_000},
    {"name": "Central African Republic", "population": 5_500_000},
    {"name": "Chad", "population": 17_700_000},
    {"name": "Chile", "population": 19_600_000},
    {"name": "China", "population": 1_411_000_000},
    {"name": "Colombia", "population": 52_000_000},
    {"name": "Comoros", "population": 836_000},
    {"name": "Congo (Brazzaville)", "population": 5_900_000},
    {"name": "Congo (Kinshasa)", "population": 99_000_000},
    {"name": "Costa Rica", "population": 5_200_000},
    {"name": "Croatia", "population": 3_850_000},
    {"name": "Cuba", "population": 11_000_000},
    {"name": "Cyprus", "population": 1_250_000},
    {"name": "Czech Republic", "population": 10_500_000},
    {"name": "Denmark", "population": 5_900_000},
    {"name": "Djibouti", "population": 1_120_000},
    {"name": "Dominica", "population": 72_000},
    {"name": "Dominican Republic", "population": 11_200_000},
    {"name": "Ecuador", "population": 18_000_000},
    {"name": "Egypt", "population": 110_000_000},
    {"name": "El Salvador", "population": 6_300_000},
    {"name": "Equatorial Guinea", "population": 1_670_000},
    {"name": "Eritrea", "population": 3_680_000},
    {"name": "Estonia", "population": 1_330_000},
    {"name": "Eswatini", "population": 1_200_000},
    {"name": "Ethiopia", "population": 120_000_000},
    {"name": "Fiji", "population": 929_000},
    {"name": "Finland", "population": 5_550_000},
    {"name": "France", "population": 68_000_000},
    {"name": "Gabon", "population": 2_380_000},
    {"name": "Gambia", "population": 2_700_000},
    {"name": "Georgia", "population": 3_700_000},
    {"name": "Germany", "population": 83_000_000},
    {"name": "Ghana", "population": 33_000_000},
    {"name": "Greece", "population": 10_400_000},
    {"name": "Grenada", "population": 125_000},
    {"name": "Guatemala", "population": 17_800_000},
    {"name": "Guinea", "population": 13_800_000},
    {"name": "Guinea-Bissau", "population": 2_100_000},
    {"name": "Guyana", "population": 808_000},
    {"name": "Haiti", "population": 11_500_000},
    {"name": "Honduras", "population": 10_400_000},
    {"name": "Hungary", "population": 9_600_000},
    {"name": "Iceland", "population": 375_000},
    {"name": "India", "population": 1_428_000_000},
    {"name": "Indonesia", "population": 277_000_000},
    {"name": "Iran", "population": 88_500_000},
    {"name": "Iraq", "population": 44_500_000},
    {"name": "Ireland", "population": 5_050_000},
    {"name": "Israel", "population": 9_750_000},
    {"name": "Italy", "population": 59_000_000},
    {"name": "Jamaica", "population": 2_820_000},
    {"name": "Japan", "population": 125_000_000},
    {"name": "Jordan", "population": 11_200_000},
    {"name": "Kazakhstan", "population": 19_600_000},
    {"name": "Kenya", "population": 55_000_000},
    {"name": "Kiribati", "population": 131_000},
    {"name": "North Korea", "population": 26_000_000},
    {"name": "South Korea", "population": 51_000_000},
    {"name": "Kuwait", "population": 4_260_000},
    {"name": "Kyrgyzstan", "population": 6_900_000},
    {"name": "Laos", "population": 7_500_000},
    {"name": "Latvia", "population": 1_880_000},
    {"name": "Lebanon", "population": 5_300_000},
    {"name": "Lesotho", "population": 2_300_000},
    {"name": "Liberia", "population": 5_300_000},
    {"name": "Libya", "population": 6_800_000},
    {"name": "Liechtenstein", "population": 39_000},
    {"name": "Lithuania", "population": 2_860_000},
    {"name": "Luxembourg", "population": 660_000},
    {"name": "Madagascar", "population": 29_600_000},
    {"name": "Malawi", "population": 20_400_000},
    {"name": "Malaysia", "population": 33_900_000},
    {"name": "Maldives", "population": 520_000},
    {"name": "Mali", "population": 22_500_000},
    {"name": "Malta", "population": 530_000},
    {"name": "Marshall Islands", "population": 42_000},
    {"name": "Mauritania", "population": 4_700_000},
    {"name": "Mauritius", "population": 1_300_000},
    {"name": "Mexico", "population": 128_000_000},
    {"name": "Micronesia", "population": 114_000},
    {"name": "Moldova", "population": 2_500_000},
    {"name": "Monaco", "population": 39_000},
    {"name": "Mongolia", "population": 3_400_000},
    {"name": "Montenegro", "population": 620_000},
    {"name": "Morocco", "population": 37_000_000},
    {"name": "Mozambique", "population": 32_900_000},
    {"name": "Myanmar", "population": 54_000_000},
    {"name": "Namibia", "population": 2_560_000},
    {"name": "Nauru", "population": 12_500},
    {"name": "Nepal", "population": 30_500_000},
    {"name": "Netherlands", "population": 17_800_000},
    {"name": "New Zealand", "population": 5_120_000},
    {"name": "Nicaragua", "population": 6_900_000},
    {"name": "Niger", "population": 26_000_000},
    {"name": "Nigeria", "population": 220_000_000},
    {"name": "North Macedonia", "population": 2_050_000},
    {"name": "Norway", "population": 5_450_000},
    {"name": "Oman", "population": 4_500_000},
    {"name": "Pakistan", "population": 240_000_000},
    {"name": "Palau", "population": 18_000},
    {"name": "Palestine", "population": 5_370_000},
    {"name": "Panama", "population": 4_400_000},
    {"name": "Papua New Guinea", "population": 10_000_000},
    {"name": "Paraguay", "population": 6_700_000},
    {"name": "Peru", "population": 34_000_000},
    {"name": "Philippines", "population": 115_000_000},
    {"name": "Poland", "population": 37_700_000},
    {"name": "Portugal", "population": 10_300_000},
    {"name": "Qatar", "population": 2_700_000},
    {"name": "Romania", "population": 19_000_000},
    {"name": "Russia", "population": 144_000_000},
    {"name": "Rwanda", "population": 13_700_000},
    {"name": "Saint Kitts and Nevis", "population": 47_000},
    {"name": "Saint Lucia", "population": 180_000},
    {"name": "Saint Vincent", "population": 103_000},
    {"name": "Samoa", "population": 220_000},
    {"name": "San Marino", "population": 34_000},
    {"name": "Sao Tome and Principe", "population": 227_000},
    {"name": "Saudi Arabia", "population": 36_000_000},
    {"name": "Senegal", "population": 17_300_000},
    {"name": "Serbia", "population": 6_800_000},
    {"name": "Seychelles", "population": 100_000},
    {"name": "Sierra Leone", "population": 8_600_000},
    {"name": "Singapore", "population": 5_600_000},
    {"name": "Slovakia", "population": 5_400_000},
    {"name": "Slovenia", "population": 2_100_000},
    {"name": "Solomon Islands", "population": 720_000},
    {"name": "Somalia", "population": 17_500_000},
    {"name": "South Africa", "population": 60_000_000},
    {"name": "South Sudan", "population": 11_000_000},
    {"name": "Spain", "population": 47_000_000},
    {"name": "Sri Lanka", "population": 22_000_000},
    {"name": "Sudan", "population": 46_000_000},
    {"name": "Suriname", "population": 618_000},
    {"name": "Sweden", "population": 10_500_000},
    {"name": "Switzerland", "population": 8_700_000},
    {"name": "Syria", "population": 22_000_000},
    {"name": "Taiwan", "population": 23_900_000},
    {"name": "Tajikistan", "population": 10_000_000},
    {"name": "Tanzania", "population": 65_000_000},
    {"name": "Thailand", "population": 71_600_000},
    {"name": "Timor-Leste", "population": 1_340_000},
    {"name": "Togo", "population": 8_800_000},
    {"name": "Tonga", "population": 106_000},
    {"name": "Trinidad and Tobago", "population": 1_530_000},
    {"name": "Tunisia", "population": 12_300_000},
    {"name": "Turkey", "population": 85_000_000},
    {"name": "Turkmenistan", "population": 6_400_000},
    {"name": "Tuvalu", "population": 11_300},
    {"name": "Uganda", "population": 47_000_000},
    {"name": "Ukraine", "population": 38_000_000},
    {"name": "United Arab Emirates", "population": 9_400_000},
    {"name": "United Kingdom", "population": 67_000_000},
    {"name": "United States", "population": 335_000_000},
    {"name": "Uruguay", "population": 3_420_000},
    {"name": "Uzbekistan", "population": 36_000_000},
    {"name": "Vanuatu", "population": 326_000},
    {"name": "Vatican City", "population": 800},
    {"name": "Venezuela", "population": 28_800_000},
    {"name": "Vietnam", "population": 98_000_000},
    {"name": "Yemen", "population": 33_700_000},
    {"name": "Zambia", "population": 20_000_000},
    {"name": "Zimbabwe", "population": 16_300_000}
]

def calculate_initial_soldiers(pop: int) -> int:
    if pop <= 5_000_000: return 1
    elif pop <= 10_000_000: return 2
    elif pop <= 25_000_000: return 3
    elif pop <= 50_000_000: return 4
    elif pop <= 75_000_000: return 5
    elif pop <= 100_000_000: return 6
    elif pop <= 125_000_000: return 7
    elif pop <= 150_000_000: return 8
    else: return 9

# --- Database Storage Helpers ---

def save_game(game_id: str, game_data: dict):
    if USE_FIREBASE:
        db.collection("games").document(game_id).set(game_data)
    else:
        GAMES_DB[game_id] = game_data

def load_game(game_id: str) -> Optional[dict]:
    if USE_FIREBASE:
        doc = db.collection("games").document(game_id).get()
        return doc.to_dict() if doc.exists else None
    return GAMES_DB.get(game_id)

def verify_token(authorization: Optional[str] = Header(None)) -> Optional[str]:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split("Bearer ")[1]
    if not USE_FIREBASE:
        return token
    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token.get("uid")
    except Exception:
        return None

# --- Pydantic Request Models ---

class AuthRequest(BaseModel):
    email: str
    password: str

class NewGameRequest(BaseModel):
    user_id: str
    selected_country: str

class AttackRequest(BaseModel):
    game_id: str
    attacker_country: str
    defender_country: str

# --- AUTH ENDPOINTS ---

@app.post("/api/auth/signup")
def user_signup(req: AuthRequest):
    """Registers a new user account with Firebase Auth[cite: 5]."""
    if USE_FIREBASE:
        try:
            user = auth.create_user(email=req.email, password=req.password)
            return {"status": "SUCCESS", "uid": user.uid, "email": user.email}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    else:
        mock_uid = f"user_{random.randint(1000, 9999)}"
        return {"status": "SUCCESS", "uid": mock_uid, "email": req.email, "token": mock_uid}

@app.post("/api/auth/login")
def user_login(req: AuthRequest):
    """Authenticates existing user and returns Auth session token[cite: 5]."""
    if USE_FIREBASE and FIREBASE_WEB_API_KEY != "your_firebase_web_api_key_here":
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_WEB_API_KEY}"
        res = requests.post(url, json={"email": req.email, "password": req.password, "returnSecureToken": True})
        if res.status_code == 200:
            data = res.json()
            return {"status": "SUCCESS", "uid": data["localId"], "token": data["idToken"], "email": data["email"]}
        else:
            raise HTTPException(status_code=401, detail="Invalid email or password.")
    else:
        mock_uid = f"user_{req.email.split('@')[0]}"
        return {"status": "SUCCESS", "uid": mock_uid, "token": mock_uid, "email": req.email}

# --- GAME ENGINE ENDPOINTS ---

@app.get("/api/countries")
def get_country_list():
    return [c["name"] for c in ALL_COUNTRIES]

@app.get("/api/game/view/{game_id}")
def view_game(game_id: str):
    game = load_game(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game session not found.")
    return {"access": "GUEST_VIEW", "game_state": game}

@app.post("/api/game/new")
def create_new_game(req: NewGameRequest):
    user_c = next((c for c in ALL_COUNTRIES if c["name"] == req.selected_country), ALL_COUNTRIES[0])
    available = [c for c in ALL_COUNTRIES if c["name"] != req.selected_country]
    selected_9 = random.sample(available, 9)
    selected_10 = [user_c] + selected_9

    players = [req.user_id] + [f"NPC_{i}" for i in range(1, 10)]
    random.shuffle(players)

    countries = {}
    for idx, c in enumerate(selected_10):
        owner = players[idx]
        init_soldiers = calculate_initial_soldiers(c["population"])
        countries[c["name"]] = {
            "owner": owner,
            "soldiers": init_soldiers,
            "base_value": init_soldiers,
            "population": c["population"]
        }

    game_id = f"game_{random.randint(1000, 9999)}"
    game_data = {
        "game_id": game_id,
        "round": 1,
        "current_turn_index": 0,
        "turn_order": players,
        "human_player": req.user_id,
        "countries": countries,
        "game_over": False,
        "winner": None
    }
    save_game(game_id, game_data)
    return game_data

def execute_attack_logic(game: dict, att_name: str, def_name: str) -> dict:
    att = game["countries"][att_name]
    def_c = game["countries"][def_name]

    max_att = att["soldiers"] - 1
    max_def = def_c["soldiers"]
    dice_count = min(max_att, max_def)

    att_rolls = [random.randint(1, 6) for _ in range(dice_count)]
    def_rolls = [random.randint(1, 6) for _ in range(dice_count)]

    att_losses = 0
    def_losses = 0
    for i in range(dice_count):
        if att_rolls[i] > def_rolls[i]:
            def_losses += 1
        elif def_rolls[i] > att_rolls[i]:
            att_losses += 1

    att["soldiers"] -= att_losses
    def_c["soldiers"] -= def_losses

    conquered = False
    if def_c["soldiers"] <= 0:
        conquered = True
        def_c["owner"] = att["owner"]
        gained = max(2, math.floor(def_c["base_value"] / 2))
        def_c["soldiers"] = gained

    return {
        "att_rolls": att_rolls,
        "def_rolls": def_rolls,
        "att_losses": att_losses,
        "def_losses": def_losses,
        "conquered": conquered
    }

@app.post("/api/game/attack")
def process_human_attack(req: AttackRequest, authorization: Optional[str] = Header(None)):
    user_uid = verify_token(authorization)
    game = load_game(req.game_id)
    if not game or game["game_over"]:
        raise HTTPException(status_code=400, detail="Invalid game session")

    if user_uid and user_uid != game["human_player"]:
        raise HTTPException(status_code=403, detail="Unauthorized: Guest viewers cannot make moves.")

    res = execute_attack_logic(game, req.attacker_country, req.defender_country)

    prompt = (
        f"Geopolitical battle: {req.attacker_country} attacked {req.defender_country}. "
        f"Attacker rolls: {res['att_rolls']}, Defender rolls: {res['def_rolls']}. "
        f"Attacker lost {res['att_losses']} soldiers, Defender lost {res['def_losses']} soldiers. "
        f"{'Territory Conquered!' if res['conquered'] else 'Defenders held their ground.'}"
    )

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=80
        )
        commentary = completion.choices[0].message.content.strip()
    except Exception:
        commentary = f"Battle resolved. Attacker lost {res['att_losses']}, Defender lost {res['def_losses']}."

    save_game(req.game_id, game)

    return {
        "attacker_roll": res["att_rolls"][0] if res["att_rolls"] else 1,
        "defender_roll": res["def_rolls"][0] if res["def_rolls"] else 1,
        "commentary": commentary,
        "game_state": game
    }

@app.post("/api/game/npc-turn")
def execute_npc_turn(game_id: str):
    game = load_game(game_id)
    if not game or game["game_over"]:
        raise HTTPException(status_code=400, detail="Invalid or completed game")

    current_player = game["turn_order"][game["current_turn_index"]]
    if current_player == game["human_player"]:
        return {"status": "WAITING_FOR_HUMAN", "message": "It is the human player's turn."}

    npc_countries = [name for name, info in game["countries"].items() if info["owner"] == current_player]

    if not npc_countries:
        game["current_turn_index"] = (game["current_turn_index"] + 1) % len(game["turn_order"])
        save_game(game_id, game)
        return {
            "status": "ELIMINATED",
            "npc": current_player,
            "action": f"{current_player} has been eliminated.",
            "justification": "No remaining controlled territories."
        }

    if game["round"] >= 2:
        reinforcements = len(npc_countries) * 2
        primary_country = max(npc_countries, key=lambda c: game["countries"][c]["soldiers"])
        game["countries"][primary_country]["soldiers"] += reinforcements

    best_attacker = None
    best_target = None
    max_advantage = 0

    for att in npc_countries:
        att_soldiers = game["countries"][att]["soldiers"]
        if att_soldiers < 2:
            continue

        for target, target_info in game["countries"].items():
            if target_info["owner"] != current_player:
                advantage = att_soldiers - target_info["soldiers"]
                if advantage > max_advantage:
                    max_advantage = advantage
                    best_attacker = att
                    best_target = target

    turn_action = ""
    reasoning = ""
    combat_data = None

    if best_attacker and best_target and max_advantage >= 2:
        res = execute_attack_logic(game, best_attacker, best_target)
        combat_data = res
        reasoning = f"Strategic Analysis: {best_attacker} holds a +{max_advantage} soldier margin over target {best_target}. Executed invasion."
        turn_action = f"{current_player} attacked {best_target} from {best_attacker}!"
    else:
        reasoning = "Strategic Analysis: No enemy target offered a safe advantage (requires >= 2 margin). Skipped turn to preserve forces."
        turn_action = f"{current_player} skipped turn."

    game["current_turn_index"] = (game["current_turn_index"] + 1) % len(game["turn_order"])
    if game["current_turn_index"] == 0:
        game["round"] += 1

    save_game(game_id, game)

    return {
        "status": "SUCCESS",
        "npc": current_player,
        "action": turn_action,
        "justification": reasoning,
        "combat": combat_data,
        "next_player": game["turn_order"][game["current_turn_index"]],
        "game_state": game
    }
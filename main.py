import random
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import battle
import pokeapi
from models import (
    EvolveRequest,
    TournamentStartRequest,
    TrainRequest,
    TripleBattleTurnRequest,
    TurnExecuteRequest,
)

kanto_pokemon_list = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    global kanto_pokemon_list
    kanto_pokemon_list = pokeapi.load_kanto_list()
    yield


app = FastAPI(title="Pokédex Kanto Ultra", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "kanto_list": kanto_pokemon_list,
        },
    )


@app.get("/pokedex", response_class=HTMLResponse)
def pokedex_view(request: Request):
    return templates.TemplateResponse(
        "pokedex.html",
        {
            "request": request,
            "kanto_list": kanto_pokemon_list,
        },
    )


@app.get("/api/pokemon/{identifier}")
def api_get_pokemon(identifier: str):
    data = pokeapi.get_pokemon_details(identifier)
    if not data:
        raise HTTPException(
            status_code=404, detail="Pokémon não encontrado."
        )
    return data


@app.get("/api/ranks")
def api_get_ranks():
    """Retorna os 151 Pokémon agrupados por Rank (S, A, B, C, D)."""
    grouped = {"S": [], "A": [], "B": [], "C": [], "D": []}
    for mon in kanto_pokemon_list:
        tier = mon.get("rank", "D")
        if tier in grouped:
            grouped[tier].append(mon)
    return {
        "ranks": grouped,
        "counts": {k: len(v) for k, v in grouped.items()},
    }


@app.post("/api/player/train")
def api_player_train(req: TrainRequest):
    """Executa uma sessão de treino para o Pokémon do jogador."""
    if req.coins < 50:
        raise HTTPException(status_code=400, detail="PokéMoedas insuficientes (Custo: 50).")

    bonus = dict(req.bonus_stats)
    bonus[req.train_type] = bonus.get(req.train_type, 0) + 3

    new_xp = req.current_xp + 100
    new_level = req.current_level
    leveled_up = False

    xp_needed = new_level * 100
    while new_xp >= xp_needed and new_level < 50:
        new_xp -= xp_needed
        new_level += 1
        leveled_up = True
        xp_needed = new_level * 100

    return {
        "success": True,
        "bonus_stats": bonus,
        "level": new_level,
        "xp": new_xp,
        "xp_needed": new_level * 100,
        "leveled_up": leveled_up,
        "coins": req.coins - 50,
        "message": f"Treino de {req.train_type.upper()} concluído com sucesso! (+3 Atributo, +100 XP)",
    }


@app.post("/api/player/evolve")
def api_player_evolve(req: EvolveRequest):
    """Executa a evolução do Pokémon para o próximo estágio."""
    target_data = pokeapi.get_pokemon_details(str(req.target_id))
    if not target_data:
        raise HTTPException(status_code=404, detail="Pokémon de destino da evolução não encontrado.")

    return {
        "success": True,
        "pokemon": target_data,
        "message": f"✨ Parabéns! Seu parceiro evoluiu para {target_data['name']}!",
    }


@app.post("/api/tournament/start")
def api_tournament_start(req: TournamentStartRequest):
    """Gera uma chave de torneio com equipes de 3 Pokémon balanceadas por Rank."""
    tier = req.tier.upper()
    pool = [p for p in kanto_pokemon_list if p.get("rank") == tier]
    if not pool:
        pool = kanto_pokemon_list

    player_lvl = max(1, req.player_level)

    rank_base_levels = {"D": 5, "C": 16, "B": 26, "A": 36, "S": 45}
    base_lvl = max(player_lvl, rank_base_levels.get(tier, 5))

    used_names = random.sample(battle.TRAINER_NAMES, min(7, len(battle.TRAINER_NAMES)))

    opponents = []
    for i, t_name in enumerate(used_names):
        # Nível por rodada (0: Quartas, 1: Semis, 2: Final)
        if i == 0:
            opp_lvl = base_lvl
        elif i == 1:
            opp_lvl = base_lvl + 1
        elif i == 2:
            opp_lvl = base_lvl + 2
        else:
            opp_lvl = max(5, base_lvl + random.randint(-1, 1))

        opp_lvl = min(50, opp_lvl)

        # Sorteia equipe de 3 Pokémon para o oponente
        team_metas = random.sample(pool, min(3, len(pool)))
        team_members = []
        for tm in team_metas:
            p_det = pokeapi.get_pokemon_details(str(tm["id"]))
            scaled = battle.calculate_scaled_stats(p_det["stats"], opp_lvl, {})
            team_members.append({
                "id": p_det["id"],
                "name": p_det["name"],
                "types": p_det["types"],
                "sprite": p_det["sprite"],
                "sprite_animated": p_det.get("sprite_animated"),
                "level": opp_lvl,
                "stats": p_det["stats"],
                "current_hp": scaled["max_hp"],
                "max_hp": scaled["max_hp"],
                "status": None,
                "sleep_turns": 0,
                "stat_buffs": {"attack": 1.0, "defense": 1.0, "speed": 1.0},
                "moves": p_det.get("moves", battle.get_pokemon_moveset(p_det["primary_type"])),
            })

        opponents.append({
            "trainer_name": t_name,
            "level": opp_lvl,
            "pokemon": team_members[0],
            "team": team_members,
        })

    return {
        "tier": tier,
        "tier_info": pokeapi.calculate_pokemon_rank(580 if tier == "S" else 500 if tier == "A" else 450 if tier == "B" else 380 if tier == "C" else 300),
        "opponents": opponents,
    }


@app.post("/api/battle/turn")
def api_battle_turn(req: TurnExecuteRequest):
    """Executa 1 turno de combate tático 3v3 com 4 golpes, prioridade, status e troca."""
    return battle.resolve_single_turn(
        player_team=req.player_team,
        opponent_team=req.opponent_team,
        p_idx=req.player_active_idx,
        o_idx=req.opponent_active_idx,
        action_type=req.player_action.type,
        action_index=req.player_action.index,
        trainer_name=req.opponent_trainer_name,
    )


@app.post("/api/battle/triple_turn")
def api_battle_triple_turn(req: TripleBattleTurnRequest):
    """Executa 1 rodada completa de Batalha Tripla (3v3 Simultâneo) com resolução unificada por Velocidade."""
    return battle.resolve_triple_turn(
        player_team=req.player_team,
        opponent_team=req.opponent_team,
        player_orders=req.player_orders,
        trainer_name=req.opponent_trainer_name,
    )

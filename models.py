"""Modelos Pydantic dos corpos de requisição das rotas em main.py."""
from typing import Dict, List

from pydantic import BaseModel


class TrainRequest(BaseModel):
    pokemon_id: int
    current_level: int
    current_xp: int
    train_type: str  # "attack", "defense", "speed", "hp"
    bonus_stats: Dict[str, int] = {}
    coins: int


class EvolveRequest(BaseModel):
    current_id: int
    target_id: int
    level: int
    bonus_stats: Dict[str, int] = {}


class TournamentStartRequest(BaseModel):
    tier: str  # "D", "C", "B", "A", "S"
    player_level: int = 10


class BattleAction(BaseModel):
    type: str  # "move" ou "switch"
    index: int  # 0..3 para golpe, 0..2 para troca de pokemon


class TurnExecuteRequest(BaseModel):
    player_team: List[dict]
    player_active_idx: int
    opponent_team: List[dict]
    opponent_active_idx: int
    opponent_trainer_name: str
    player_action: BattleAction


class PokemonOrder(BaseModel):
    pokemon_idx: int  # 0, 1, 2
    move_idx: int  # 0..3
    target_idx: int  # 0, 1, 2


class TripleBattleTurnRequest(BaseModel):
    player_team: List[dict]
    opponent_team: List[dict]
    player_orders: List[PokemonOrder]
    opponent_trainer_name: str

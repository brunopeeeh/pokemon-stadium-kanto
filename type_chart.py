"""Tabela de efetividade de tipos (PokeAPI REST), isolada porque é usada tanto
pelo cliente de dados (matchups defensivos de um Pokémon) quanto pelo motor de
batalha (multiplicador de dano de um golpe) — evita import circular entre os dois.
"""
import requests

REST_TYPE_URL = "https://pokeapi.co/api/v2/type/{name}"

type_damage_cache = {}


def get_type_damage_relations(type_name: str):
    """Busca as relações de dano de um tipo com cache em memória."""
    type_name = type_name.lower()
    if type_name in type_damage_cache:
        return type_damage_cache[type_name]

    res = requests.get(REST_TYPE_URL.format(name=type_name), timeout=5)
    if res.status_code == 200:
        data = res.json().get("damage_relations", {})
        type_damage_cache[type_name] = data
        return data
    return {}

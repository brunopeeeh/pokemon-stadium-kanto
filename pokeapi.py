"""Cliente da PokeAPI (GraphQL + REST): lista de Kanto, detalhes de um Pokémon
(stats, matchups, cadeia de evolução, moveset) e classificação por Rank.
"""
from collections import defaultdict

import requests

from battle import get_pokemon_moveset
from type_chart import get_type_damage_relations

GRAPHQL_URL = "https://beta.pokeapi.co/graphql/v1beta"
REST_SPECIES_URL = "https://pokeapi.co/api/v2/pokemon-species/{id}"
POKESPRITE_BASE = "https://raw.githubusercontent.com/msikma/pokesprite/master/pokemon-gen8/regular/{slug}.png"
POKEMON_CRY_BASE = "https://raw.githubusercontent.com/PokeAPI/cries/main/cries/pokemon/latest/{id}.ogg"

pokemon_details_cache = {}


def calculate_pokemon_rank(bst: int) -> dict:
    """Classifica o Pokémon nos Ranks D, C, B, A ou S com base no BST (Base Stat Total)."""
    if bst >= 580:
        return {
            "tier": "S",
            "name": "Rank S (Lendário / Titã)",
            "color": "#FFD700",
            "badge_bg": "linear-gradient(135deg, #FFD700, #FF8F00)",
            "desc": "Lendários, Míticos e Pseudo-Lendários",
        }
    elif bst >= 490:
        return {
            "tier": "A",
            "name": "Rank A (Elite)",
            "color": "#E040FB",
            "badge_bg": "linear-gradient(135deg, #E040FB, #7C4DFF)",
            "desc": "Formas finais de alto desempenho competitivo",
        }
    elif bst >= 430:
        return {
            "tier": "B",
            "name": "Rank B (Avançado)",
            "color": "#00E5FF",
            "badge_bg": "linear-gradient(135deg, #00E5FF, #0091EA)",
            "desc": "Evoluções sólidas e Pokémon veteranos",
        }
    elif bst >= 340:
        return {
            "tier": "C",
            "name": "Rank C (Intermediário)",
            "color": "#76FF03",
            "badge_bg": "linear-gradient(135deg, #76FF03, #43A047)",
            "desc": "Estágios intermediários e Pokémon de suporte",
        }
    else:
        return {
            "tier": "D",
            "name": "Rank D (Iniciante)",
            "color": "#B0BEC5",
            "badge_bg": "linear-gradient(135deg, #B0BEC5, #78909C)",
            "desc": "Iniciais base, formas não evoluídas e primeiras rotas",
        }


def load_kanto_list():
    query = """
    query {
      pokemon_v2_pokemon(where: {id: {_lte: 151}}, order_by: {id: asc}) {
        id
        name
        pokemon_v2_pokemonstats {
          base_stat
        }
      }
    }
    """
    try:
        res = requests.post(GRAPHQL_URL, json={"query": query}, timeout=10)
        if res.status_code == 200:
            raw_list = res.json().get("data", {}).get("pokemon_v2_pokemon", [])
            processed = []
            for item in raw_list:
                bst = sum(
                    s["base_stat"]
                    for s in item.get("pokemon_v2_pokemonstats", [])
                )
                rank_info = calculate_pokemon_rank(bst)
                processed.append(
                    {
                        "id": item["id"],
                        "name": item["name"],
                        "bst": bst,
                        "rank": rank_info["tier"],
                        "rank_info": rank_info,
                    }
                )
            return processed
    except Exception as e:
        print(f"Erro ao carregar lista de Kanto: {e}")
    return []


def calculate_type_matchups(types: list):
    """Calcula fraquezas, resistências e imunidades com base nos tipos defensivos."""
    multipliers = defaultdict(lambda: 1.0)

    for t in types:
        relations = get_type_damage_relations(t)
        for d in relations.get("double_damage_from", []):
            multipliers[d["name"]] *= 2.0
        for h in relations.get("half_damage_from", []):
            multipliers[h["name"]] *= 0.5
        for n in relations.get("no_damage_from", []):
            multipliers[n["name"]] *= 0.0

    weaknesses = []
    resistances = []
    immunities = []

    for attacking_type, mult in multipliers.items():
        if mult > 1.0:
            weaknesses.append(
                {"type": attacking_type.upper(), "multiplier": mult}
            )
        elif mult == 0.0:
            immunities.append(
                {"type": attacking_type.upper(), "multiplier": 0.0}
            )
        elif mult < 1.0:
            resistances.append(
                {"type": attacking_type.upper(), "multiplier": mult}
            )

    weaknesses.sort(key=lambda x: x["multiplier"], reverse=True)
    resistances.sort(key=lambda x: x["multiplier"])

    return {
        "weaknesses": weaknesses,
        "resistances": resistances,
        "immunities": immunities,
    }


def parse_evolution_chain(chain_node):
    """Percorre recursivamente a cadeia de evolução para extrair estágios."""
    evolutions = []

    def traverse(node):
        if not node:
            return
        species_name = node.get("species", {}).get("name", "")
        species_url = node.get("species", {}).get("url", "")
        species_id = None
        if species_url:
            parts = [p for p in species_url.split("/") if p]
            if parts and parts[-1].isdigit():
                species_id = int(parts[-1])

        if species_name and species_id:
            evolutions.append(
                {
                    "id": species_id,
                    "name": species_name.capitalize(),
                    "sprite": POKESPRITE_BASE.format(slug=species_name.lower()),
                }
            )

        for next_stage in node.get("evolves_to", []):
            traverse(next_stage)

    traverse(chain_node)
    return evolutions


def get_pokemon_details(identifier: str):
    cache_key = str(identifier).lower()
    if cache_key in pokemon_details_cache:
        return pokemon_details_cache[cache_key]

    is_id = identifier.isdigit()
    where = (
        f"{{id: {{_eq: {identifier}}}}}"
        if is_id
        else f'{{name: {{_eq: "{identifier.lower()}"}}}}'
    )

    query = f"""
    query {{
      pokemon_v2_pokemon(where: {where}, limit: 1) {{
        id
        name
        height
        weight
        pokemon_v2_pokemontypes {{ pokemon_v2_type {{ name }} }}
        pokemon_v2_pokemonstats {{ base_stat pokemon_v2_stat {{ name }} }}
      }}
    }}
    """
    try:
        res = requests.post(GRAPHQL_URL, json={"query": query}, timeout=10)
        if res.status_code == 200:
            items = res.json().get("data", {}).get("pokemon_v2_pokemon", [])
            if items:
                raw = items[0]
                poke_id = raw["id"]

                # 1. Busca dados de espécie e cadeia de evolução
                flavor = "Descrição não disponível."
                evolution_chain = []
                desc_res = requests.get(
                    REST_SPECIES_URL.format(id=poke_id), timeout=5
                )
                if desc_res.status_code == 200:
                    species_data = desc_res.json()
                    for entry in species_data.get("flavor_text_entries", []):
                        if entry["language"]["name"] == "en":
                            flavor = (
                                entry["flavor_text"]
                                .replace("\n", " ")
                                .replace("\x0c", " ")
                            )
                            break

                    evo_url = species_data.get("evolution_chain", {}).get("url")
                    if evo_url:
                        evo_res = requests.get(evo_url, timeout=5)
                        if evo_res.status_code == 200:
                            evolution_chain = parse_evolution_chain(
                                evo_res.json().get("chain", {})
                            )

                types_list = [
                    t["pokemon_v2_type"]["name"].lower()
                    for t in raw["pokemon_v2_pokemontypes"]
                ]
                matchups = calculate_type_matchups(types_list)

                stats_list = [
                    {
                        "name": s["pokemon_v2_stat"]["name"]
                        .replace("-", " ")
                        .title(),
                        "val": s["base_stat"],
                    }
                    for s in raw["pokemon_v2_pokemonstats"]
                ]
                bst = sum(s["val"] for s in stats_list)
                rank_info = calculate_pokemon_rank(bst)
                primary_t = types_list[0] if types_list else "normal"
                secondary_t = types_list[1] if len(types_list) > 1 else None

                result = {
                    "id": poke_id,
                    "name": raw["name"].capitalize(),
                    "slug": raw["name"],
                    "height": raw["height"] / 10,
                    "weight": raw["weight"] / 10,
                    "sprite": POKESPRITE_BASE.format(slug=raw["name"]),
                    "artwork": f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{poke_id}.png",
                    "sprite_animated": f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/showdown/{poke_id}.gif",
                    "cry_url": POKEMON_CRY_BASE.format(id=poke_id),
                    "flavor": flavor,
                    "types": [t.upper() for t in types_list],
                    "primary_type": primary_t,
                    "stats": stats_list,
                    "bst": bst,
                    "rank": rank_info["tier"],
                    "rank_info": rank_info,
                    "matchups": matchups,
                    "evolution_chain": evolution_chain,
                    "moves": get_pokemon_moveset(primary_t, secondary_t),
                }

                # Salva no cache tanto por ID quanto por nome
                pokemon_details_cache[str(poke_id)] = result
                pokemon_details_cache[raw["name"].lower()] = result

                return result
    except Exception as e:
        print(f"Erro ao buscar detalhes de {identifier}: {e}")
    return None

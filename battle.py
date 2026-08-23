"""Dados de jogo (golpes, treinadores) e motor de batalha: geração de moveset,
escala de status por nível, multiplicador de tipo e resolução de turnos
(1v1 com banco e 3v3 simultâneo). Não depende de nada de HTTP/FastAPI —
recebe times como listas de dicts e devolve dicts prontos para virar JSON.
"""
import random
from typing import List, Optional

from type_chart import get_type_damage_relations

MOVES_DATABASE = {
    "tackle": {"name": "Investida", "type": "normal", "power": 40, "accuracy": 100, "category": "physical", "target_type": "single", "desc": "Ataque físico rápido de alvo único."},
    "quick_attack": {"name": "Ataque Rápido", "type": "normal", "power": 40, "accuracy": 100, "category": "physical", "priority": 1, "target_type": "single", "desc": "Golpe veloz com prioridade."},
    "scratch": {"name": "Arranhão", "type": "normal", "power": 40, "accuracy": 100, "category": "physical", "target_type": "single", "desc": "Arranha com garras afiadas."},
    "ember": {"name": "Brasas", "type": "fire", "power": 45, "accuracy": 100, "category": "special", "status": "burn", "status_chance": 0.25, "target_type": "single", "desc": "Lança pequenas chamas. Chance de Queimar."},
    "flamethrower": {"name": "Lança-Chamas", "type": "fire", "power": 85, "accuracy": 100, "category": "special", "status": "burn", "status_chance": 0.2, "target_type": "single", "desc": "Jato torrencial de fogo intenso."},
    "water_gun": {"name": "Jato de Água", "type": "water", "power": 45, "accuracy": 100, "category": "special", "target_type": "single", "desc": "Dispara um jato pressurizado de água."},
    "surf": {"name": "Surfar", "type": "water", "power": 85, "accuracy": 100, "category": "special", "target_type": "all_opponents", "desc": "🌊 Golpe de Área! Atinge TODOS os 3 oponentes."},
    "vine_whip": {"name": "Chicote de Vinha", "type": "grass", "power": 45, "accuracy": 100, "category": "physical", "target_type": "single", "desc": "Chicoteia o oponente com vinhas finas."},
    "razor_leaf": {"name": "Folha Navalha", "type": "grass", "power": 65, "accuracy": 95, "category": "physical", "target_type": "all_opponents", "desc": "🍃 Golpe de Área! Lança folhas afiadas em todos os oponentes."},
    "thunder_shock": {"name": "Choque do Trovão", "type": "electric", "power": 45, "accuracy": 100, "category": "special", "status": "paralysis", "status_chance": 0.25, "target_type": "single", "desc": "Descarga elétrica. Chance de Paralisar."},
    "thunderbolt": {"name": "Raio", "type": "electric", "power": 85, "accuracy": 100, "category": "special", "status": "paralysis", "status_chance": 0.2, "target_type": "single", "desc": "Um raio potente atinge o oponente."},
    "rock_throw": {"name": "Lançamento de Rocha", "type": "rock", "power": 55, "accuracy": 90, "category": "physical", "target_type": "single", "desc": "Arremessa pedras pesadas."},
    "rock_slide": {"name": "Deslize de Pedras", "type": "rock", "power": 75, "accuracy": 90, "category": "physical", "target_type": "all_opponents", "desc": "🪨 Golpe de Área! Desaba rochas em todos os oponentes."},
    "mud_slap": {"name": "Tapa de Lama", "type": "ground", "power": 35, "accuracy": 100, "category": "special", "target_type": "single", "desc": "Joga lama no rosto do adversário."},
    "earthquake": {"name": "Terremoto", "type": "ground", "power": 90, "accuracy": 100, "category": "physical", "target_type": "all_opponents", "desc": "🌋 Golpe de Área devastador que atinge todos os oponentes."},
    "confusion": {"name": "Confusão", "type": "psychic", "power": 50, "accuracy": 100, "category": "special", "target_type": "single", "desc": "Onda telecinética que confunde a mente."},
    "psychic": {"name": "Psíquico", "type": "psychic", "power": 85, "accuracy": 100, "category": "special", "target_type": "single", "desc": "Forte poder mental esmaga o oponente."},
    "poison_sting": {"name": "Picada Venenosa", "type": "poison", "power": 40, "accuracy": 100, "category": "physical", "status": "poison", "status_chance": 0.3, "target_type": "single", "desc": "Espinho tóxico. Chance de Envenenar."},
    "sludge_bomb": {"name": "Bomba de Lodo", "type": "poison", "power": 80, "accuracy": 100, "category": "special", "status": "poison", "status_chance": 0.3, "target_type": "single", "desc": "Detona lodo corrosivo no alvo."},
    "bite": {"name": "Mordida", "type": "dark", "power": 60, "accuracy": 100, "category": "physical", "target_type": "single", "desc": "Morde com presas afiadas."},
    "iron_tail": {"name": "Cauda de Ferro", "type": "steel", "power": 70, "accuracy": 85, "category": "physical", "target_type": "single", "desc": "Bate com uma cauda dura como aço."},
    "ice_shard": {"name": "Cacos de Gelo", "type": "ice", "power": 45, "accuracy": 100, "category": "physical", "priority": 1, "target_type": "single", "desc": "Lança lâminas de gelo instantâneas."},
    "ice_beam": {"name": "Raio Congelante", "type": "ice", "power": 85, "accuracy": 100, "category": "special", "target_type": "single", "desc": "Raio gélido que congela o alvo."},
    "karate_chop": {"name": "Golpe de Caratê", "type": "fighting", "power": 55, "accuracy": 100, "category": "physical", "target_type": "single", "desc": "Golpe marcial com alta chance de crítico."},
    "wing_attack": {"name": "Ataque de Asa", "type": "flying", "power": 60, "accuracy": 100, "category": "physical", "target_type": "single", "desc": "Golpeia abrindo asas majestosas."},
    "bug_bite": {"name": "Picada de Inseto", "type": "bug", "power": 50, "accuracy": 100, "category": "physical", "target_type": "single", "desc": "Mordida rápida e voraz de inseto."},
    "dragon_breath": {"name": "Sopro do Dragão", "type": "dragon", "power": 60, "accuracy": 100, "category": "special", "status": "paralysis", "status_chance": 0.3, "target_type": "single", "desc": "Sopra energia dracônica com choque."},
    # Golpes de Status e Buffs
    "thunder_wave": {"name": "Onda de Trovão", "type": "electric", "power": 0, "accuracy": 90, "category": "status", "status": "paralysis", "status_chance": 1.0, "target_type": "single", "desc": "Paralisa o alvo (reduz velocidade em 50%)."},
    "will_o_wisp": {"name": "Fogo-Fátuo", "type": "fire", "power": 0, "accuracy": 85, "category": "status", "status": "burn", "status_chance": 1.0, "target_type": "single", "desc": "Queima o alvo (reduz ataque em 50%)."},
    "sleep_powder": {"name": "Pó do Sono", "type": "grass", "power": 0, "accuracy": 80, "category": "status", "status": "sleep", "status_chance": 1.0, "target_type": "single", "desc": "Adormece o oponente por 1-3 turnos."},
    "toxic": {"name": "Tóxico", "type": "poison", "power": 0, "accuracy": 90, "category": "status", "status": "poison", "status_chance": 1.0, "target_type": "single", "desc": "Envenena gravemente o alvo com dano contínuo."},
    "swords_dance": {"name": "Dança das Espadas", "type": "normal", "power": 0, "accuracy": 100, "category": "buff", "buff_stat": "attack", "buff_mult": 1.4, "target_type": "self", "desc": "Aumenta o Ataque próprio em +40%."},
    "iron_defense": {"name": "Defesa de Ferro", "type": "steel", "power": 0, "accuracy": 100, "category": "buff", "buff_stat": "defense", "buff_mult": 1.4, "target_type": "self", "desc": "Aumenta a Defesa própria em +40%."},
    "agility": {"name": "Agilidade", "type": "psychic", "power": 0, "accuracy": 100, "category": "buff", "buff_stat": "speed", "buff_mult": 1.5, "target_type": "self", "desc": "Aumenta a Velocidade própria em +50%."},
    "recover": {"name": "Recuperar", "type": "normal", "power": 0, "accuracy": 100, "category": "heal", "heal_pct": 0.4, "target_type": "self", "desc": "Restaura 40% do HP máximo."},
}

TRAINER_NAMES = [
    "Red", "Blue", "Misty", "Brock", "Lt. Surge", "Erika", "Koga",
    "Sabrina", "Blaine", "Giovanni", "Lorelei", "Bruno", "Agatha",
    "Lance", "Gary", "Trace", "Leaf", "Ritchie", "Green"
]


def get_pokemon_moveset(primary_type: str, secondary_type: Optional[str] = None) -> list:
    """Gera um moveset de 4 golpes estratégicos (Rápido, STAB 1, Cobertura, Status/Buff)."""
    p_type = (primary_type or "normal").lower()
    s_type = (secondary_type or "").lower()

    # Slot 1: Golpe Básico/Rápido
    slot1 = MOVES_DATABASE["quick_attack"] if p_type in ["electric", "flying", "normal"] else MOVES_DATABASE["tackle"]

    # Slot 2: STAB Primário
    type_stab_map = {
        "fire": "ember", "water": "water_gun", "grass": "vine_whip",
        "electric": "thunder_shock", "poison": "poison_sting", "rock": "rock_throw",
        "ground": "mud_slap", "psychic": "confusion", "ice": "ice_shard",
        "fighting": "karate_chop", "flying": "wing_attack", "bug": "bug_bite",
        "dragon": "dragon_breath", "steel": "iron_tail", "ghost": "confusion",
    }
    stab_key = type_stab_map.get(p_type, "tackle")
    slot2 = MOVES_DATABASE.get(stab_key, MOVES_DATABASE["tackle"])

    # Slot 3: Cobertura
    coverage_map = {
        "fire": "bite", "water": "ice_shard", "grass": "sludge_bomb",
        "electric": "iron_tail", "poison": "bite", "rock": "mud_slap",
        "ground": "rock_slide", "psychic": "sludge_bomb", "ice": "water_gun",
        "fighting": "rock_slide", "flying": "quick_attack", "bug": "poison_sting",
        "dragon": "flamethrower", "normal": "bite"
    }
    cov_key = coverage_map.get(p_type, "bite")
    slot3 = MOVES_DATABASE.get(cov_key, MOVES_DATABASE["bite"])

    # Slot 4: Status ou Buff
    status_map = {
        "electric": "thunder_wave", "fire": "will_o_wisp", "grass": "sleep_powder",
        "poison": "toxic", "psychic": "agility", "steel": "iron_defense",
        "fighting": "swords_dance", "rock": "iron_defense", "ground": "iron_defense",
        "water": "recover", "normal": "swords_dance"
    }
    stat_key = status_map.get(p_type, "swords_dance")
    slot4 = MOVES_DATABASE.get(stat_key, MOVES_DATABASE["swords_dance"])

    return [slot1, slot2, slot3, slot4]


def calculate_scaled_stats(base_stats: list, level: int, bonus: dict = None) -> dict:
    bonus = bonus or {}
    stat_dict = {}
    for s in base_stats:
        name = s["name"].lower()
        val = s["val"]
        stat_dict[name] = val

    lvl = max(1, level)
    hp_base = stat_dict.get("hp", 45)
    atk_base = max(stat_dict.get("attack", 45), stat_dict.get("special attack", 45))
    def_base = max(stat_dict.get("defense", 45), stat_dict.get("special defense", 45))
    spd_base = stat_dict.get("speed", 45)

    # Fórmula clássica proporcional ao nível (Ex: Nv. 5 tem ~20 HP; Nv. 50 tem ~120 HP)
    max_hp = int((2 * hp_base * lvl) / 100 + lvl + 10 + bonus.get("hp", 0) * 2)
    attack = int((2 * atk_base * lvl) / 100 + 5 + bonus.get("attack", 0))
    defense = int((2 * def_base * lvl) / 100 + 5 + bonus.get("defense", 0))
    speed = int((2 * spd_base * lvl) / 100 + 5 + bonus.get("speed", 0))

    return {
        "max_hp": max_hp,
        "current_hp": max_hp,
        "attack": attack,
        "defense": defense,
        "speed": speed,
    }


def get_type_multiplier(attacker_types: list, defender_types: list) -> float:
    """Calcula o melhor multiplicador de dano dos tipos do atacante contra os tipos do defensor."""
    best_mult = 1.0
    for atk_t in attacker_types:
        atk_t_lower = atk_t.lower()
        move_mult = 1.0
        for def_t in defender_types:
            def_relations = get_type_damage_relations(def_t.lower())
            if any(d["name"] == atk_t_lower for d in def_relations.get("double_damage_from", [])):
                move_mult *= 2.0
            elif any(h["name"] == atk_t_lower for h in def_relations.get("half_damage_from", [])):
                move_mult *= 0.5
            elif any(n["name"] == atk_t_lower for n in def_relations.get("no_damage_from", [])):
                move_mult *= 0.0
        if move_mult > best_mult:
            best_mult = move_mult
    return best_mult


def get_triple_valid_targets(pos: int, enemy_team: List[dict]) -> List[int]:
    """Retorna os índices válidos dos oponentes alcançáveis pela posição no campo."""
    alive_indices = [i for i, m in enumerate(enemy_team) if m.get("current_hp", 0) > 0]
    if not alive_indices:
        return []

    # Alcance padrão de Batalha Tripla
    reach_map = {
        0: [0, 1],       # Esquerda alcança Esquerda e Centro
        1: [0, 1, 2],    # Centro alcança todos os 3
        2: [1, 2],       # Direita alcança Centro e Direita
    }
    in_reach = [i for i in reach_map.get(pos, [0, 1, 2]) if i in alive_indices]
    # Se nenhum oponente no alcance padrão estiver vivo, alcança qualquer sobrevivente
    return in_reach if in_reach else alive_indices


def resolve_single_turn(player_team, opponent_team, p_idx, o_idx, action_type, action_index, trainer_name):
    """Executa 1 turno de combate 1v1 ativo (com banco de 3) com prioridade, status e troca."""
    p_mon = player_team[p_idx]
    o_mon = opponent_team[o_idx]

    logs = []

    # 1. Se o Pokémon do jogador estava desmaiado e o jogador escolheu o substituto:
    if p_mon.get("current_hp", 0) <= 0 and action_type == "switch":
        p_idx = action_index
        p_mon = player_team[p_idx]
        logs.append(f"🔄 Você enviou {p_mon['name']} para o combate!")
        return {
            "player_team": player_team,
            "player_active_idx": p_idx,
            "opponent_team": opponent_team,
            "opponent_active_idx": o_idx,
            "logs": logs,
            "is_finished": False,
            "winner": None,
        }

    # 2. Escolha da IA
    ai_moves = o_mon.get("moves", [])
    best_move_idx = 0
    best_score = -1
    for m_i, m in enumerate(ai_moves):
        score = m.get("power", 0)
        m_mult = get_type_multiplier([m.get("type", "normal")], p_mon.get("types", ["NORMAL"]))
        score *= m_mult
        if m.get("category") == "status" and not p_mon.get("status"):
            score = 75
        if score > best_score:
            best_score = score
            best_move_idx = m_i

    ai_move = ai_moves[best_move_idx] if ai_moves else MOVES_DATABASE["tackle"]

    # 3. Ação do jogador
    p_switched = False
    if action_type == "switch" and action_index != p_idx and player_team[action_index]["current_hp"] > 0:
        p_idx = action_index
        p_mon = player_team[p_idx]
        logs.append(f"🔄 Você recolheu seu Pokémon e enviou {p_mon['name']}!")
        p_switched = True

    # Velocidades
    p_spd = calculate_scaled_stats(p_mon.get("stats", []), p_mon.get("level", 5), p_mon.get("bonus_stats", {}))["speed"]
    p_spd *= p_mon.get("stat_buffs", {}).get("speed", 1.0)
    if p_mon.get("status") == "paralysis":
        p_spd *= 0.5

    o_spd = calculate_scaled_stats(o_mon.get("stats", []), o_mon.get("level", 5))["speed"]
    o_spd *= o_mon.get("stat_buffs", {}).get("speed", 1.0)
    if o_mon.get("status") == "paralysis":
        o_spd *= 0.5

    p_move = p_mon.get("moves", [])[action_index] if action_type == "move" and action_index < len(p_mon.get("moves", [])) else MOVES_DATABASE["tackle"]

    p_prio = p_move.get("priority", 0) if action_type == "move" else 99
    o_prio = ai_move.get("priority", 0)

    if p_prio > o_prio:
        first = "player"
    elif o_prio > p_prio:
        first = "opponent"
    else:
        first = "player" if p_spd >= o_spd else "opponent"

    actions_queue = []
    if first == "player":
        if not p_switched:
            actions_queue.append(("player", p_mon, o_mon, p_move))
        actions_queue.append(("opponent", o_mon, p_mon, ai_move))
    else:
        actions_queue.append(("opponent", o_mon, p_mon, ai_move))
        if not p_switched:
            actions_queue.append(("player", p_mon, o_mon, p_move))

    # Executa os golpes
    for side, attacker, defender, move in actions_queue:
        if attacker["current_hp"] <= 0 or defender["current_hp"] <= 0:
            continue

        name_atk = f"Seu {attacker['name']}" if side == "player" else f"{trainer_name} com {attacker['name']}"
        name_def = f"Seu {defender['name']}" if side != "player" else f"{defender['name']} do oponente"

        # Verifica Sono
        if attacker.get("status") == "sleep":
            attacker["sleep_turns"] = attacker.get("sleep_turns", 2) - 1
            if attacker["sleep_turns"] <= 0:
                attacker["status"] = None
                logs.append(f"✨ {name_atk} acordou!")
            else:
                logs.append(f"💤 {name_atk} está dormindo e não pôde agir!")
                continue

        # Verifica Paralisia
        if attacker.get("status") == "paralysis" and random.random() < 0.25:
            logs.append(f"⚡ {name_atk} está paralisado e não conseguiu se mover!")
            continue

        # Precisão do golpe
        if random.random() * 100 > move.get("accuracy", 100):
            logs.append(f"💨 {name_atk} usou {move['name']}, mas errou o alvo!")
            continue

        # Categorias especiais
        if move.get("category") == "buff":
            buff_stat = move.get("buff_stat", "attack")
            mult = move.get("buff_mult", 1.4)
            if "stat_buffs" not in attacker:
                attacker["stat_buffs"] = {}
            attacker["stat_buffs"][buff_stat] = attacker["stat_buffs"].get(buff_stat, 1.0) * mult
            logs.append(f"💪 {name_atk} usou {move['name']}! Seu {buff_stat.upper()} aumentou!")
            continue

        if move.get("category") == "heal":
            heal = int(attacker["max_hp"] * move.get("heal_pct", 0.4))
            attacker["current_hp"] = min(attacker["max_hp"], attacker["current_hp"] + heal)
            logs.append(f"💚 {name_atk} usou {move['name']} e recuperou {heal} HP! ({attacker['current_hp']}/{attacker['max_hp']})")
            continue

        if move.get("category") == "status":
            st = move.get("status")
            if not defender.get("status"):
                defender["status"] = st
                if st == "sleep":
                    defender["sleep_turns"] = random.randint(1, 3)
                status_names = {"paralysis": "⚡ Paralisado", "burn": "🔥 Queimado", "sleep": "💤 Adormecido", "poison": "☠️ Envenenado"}
                logs.append(f"✨ {name_atk} usou {move['name']}! {name_def} ficou {status_names.get(st, st)}!")
            else:
                logs.append(f"{name_atk} usou {move['name']}, mas {name_def} já possui uma condição de status!")
            continue

        # Ataque de Dano
        lvl = attacker.get("level", 5)
        p_stats = calculate_scaled_stats(attacker.get("stats", []), lvl, attacker.get("bonus_stats", {}))
        d_stats = calculate_scaled_stats(defender.get("stats", []), defender.get("level", 5), defender.get("bonus_stats", {}))

        atk_val = p_stats["attack"] * attacker.get("stat_buffs", {}).get("attack", 1.0)
        def_val = d_stats["defense"] * defender.get("stat_buffs", {}).get("defense", 1.0)

        if attacker.get("status") == "burn" and move.get("category") == "physical":
            atk_val *= 0.5

        m_type = move.get("type", "normal")
        type_mult = get_type_multiplier([m_type], defender.get("types", ["NORMAL"]))
        crit = 1.5 if random.random() < 0.10 else 1.0
        pwr = move.get("power", 40)

        base_dmg = (((2 * lvl / 5 + 2) * pwr * (atk_val / max(def_val, 1))) / 50) + 2
        dmg = max(1, int(base_dmg * type_mult * crit * random.uniform(0.88, 1.05)))

        eff_text = ""
        if type_mult >= 2.0:
            eff_text = " 💥 Super Efetivo!"
        elif type_mult <= 0.5 and type_mult > 0:
            eff_text = " 🛡️ Pouco efetivo..."
        elif type_mult == 0.0:
            eff_text = " ⛔ Não teve efeito!"

        crit_text = " ⚡ Golpe Crítico!" if crit > 1.0 else ""

        defender["current_hp"] = max(0, defender["current_hp"] - dmg)
        logs.append(f"⚔️ {name_atk} usou {move['name']} causando {dmg} de dano!{eff_text}{crit_text} ({defender['current_hp']}/{defender['max_hp']} HP)")

        # Chance secundária de aplicar status
        if move.get("status") and not defender.get("status") and defender["current_hp"] > 0:
            if random.random() < move.get("status_chance", 0):
                st = move["status"]
                defender["status"] = st
                if st == "sleep":
                    defender["sleep_turns"] = random.randint(1, 3)
                status_names = {"paralysis": "⚡ Paralisado", "burn": "🔥 Queimado", "sleep": "💤 Adormecido", "poison": "☠️ Envenenado"}
                logs.append(f"💥 Efeito secundário! {name_def} ficou {status_names.get(st, st)}!")

        # Nocaute
        if defender["current_hp"] <= 0:
            logs.append(f"💀 {name_def} foi nocauteado!")

    # 4. Dano contínuo de status
    for mon, side_name in [(p_mon, "Seu"), (o_mon, f"{trainer_name} com")]:
        if mon["current_hp"] > 0:
            if mon.get("status") == "burn":
                burn_dmg = max(1, int(mon["max_hp"] * 0.08))
                mon["current_hp"] = max(0, mon["current_hp"] - burn_dmg)
                logs.append(f"🔥 {side_name} {mon['name']} sofreu {burn_dmg} de dano pela queimadura! ({mon['current_hp']}/{mon['max_hp']})")
            elif mon.get("status") == "poison":
                psn_dmg = max(1, int(mon["max_hp"] * 0.10))
                mon["current_hp"] = max(0, mon["current_hp"] - psn_dmg)
                logs.append(f"☠️ {side_name} {mon['name']} sofreu {psn_dmg} de dano pelo veneno! ({mon['current_hp']}/{mon['max_hp']})")

    # 5. IA envia próximo Pokémon caso o ativo tenha sido derrotado
    if o_mon["current_hp"] <= 0:
        next_o = next((i for i, m in enumerate(opponent_team) if m["current_hp"] > 0), None)
        if next_o is not None:
            o_idx = next_o
            logs.append(f"🚀 {trainer_name} enviou {opponent_team[o_idx]['name']} para a batalha!")

    # 6. Fim do combate
    player_wiped = all(m["current_hp"] <= 0 for m in player_team)
    opponent_wiped = all(m["current_hp"] <= 0 for m in opponent_team)

    is_finished = player_wiped or opponent_wiped
    winner = "player" if opponent_wiped else "opponent" if player_wiped else None
    xp_earned = 250 if winner == "player" else 80 if winner == "opponent" else 0
    coins_earned = 180 if winner == "player" else 50 if winner == "opponent" else 0

    return {
        "player_team": player_team,
        "player_active_idx": p_idx,
        "opponent_team": opponent_team,
        "opponent_active_idx": o_idx,
        "logs": logs,
        "is_finished": is_finished,
        "winner": winner,
        "xp_earned": xp_earned,
        "coins_earned": coins_earned,
    }


def resolve_triple_turn(player_team, opponent_team, player_orders, trainer_name):
    """Executa 1 rodada completa de Batalha Tripla (3v3 Simultâneo) com resolução unificada por Velocidade."""
    logs = []
    steps = []

    pos_names = ["Esquerda", "Centro", "Direita"]

    # 1. Monta as ordens da IA para os Pokémon vivos do oponente
    ai_orders = []
    for o_idx, o_mon in enumerate(opponent_team):
        if o_mon.get("current_hp", 0) <= 0:
            continue
        valid_targets = get_triple_valid_targets(o_idx, player_team)
        if not valid_targets:
            continue

        ai_moves = o_mon.get("moves", [])
        best_move_idx = 0
        best_target = valid_targets[0]
        best_score = -1

        for m_idx, m in enumerate(ai_moves):
            if m.get("target_type") == "all_opponents":
                score = m.get("power", 50) * 1.5
                if score > best_score:
                    best_score = score
                    best_move_idx = m_idx
                    best_target = valid_targets[0]
            else:
                for t_idx in valid_targets:
                    p_target = player_team[t_idx]
                    mult = get_type_multiplier([m.get("type", "normal")], p_target.get("types", ["NORMAL"]))
                    score = m.get("power", 40) * mult
                    if m.get("category") == "status" and not p_target.get("status"):
                        score = 75
                    if score > best_score:
                        best_score = score
                        best_move_idx = m_idx
                        best_target = t_idx

        ai_orders.append({
            "pokemon_idx": o_idx,
            "move_idx": best_move_idx,
            "target_idx": best_target
        })

    # 2. Enfileira todas as ações (Jogador e Oponente) com cálculo de Velocidade
    actions_queue = []

    # Ordens do Jogador
    for order in player_orders:
        p_idx = order.pokemon_idx
        if p_idx >= len(player_team):
            continue
        p_mon = player_team[p_idx]
        if p_mon.get("current_hp", 0) <= 0:
            continue

        moves = p_mon.get("moves", [])
        move = moves[order.move_idx] if order.move_idx < len(moves) else MOVES_DATABASE["tackle"]

        spd = calculate_scaled_stats(p_mon.get("stats", []), p_mon.get("level", 5), p_mon.get("bonus_stats", {}))["speed"]
        spd *= p_mon.get("stat_buffs", {}).get("speed", 1.0)
        if p_mon.get("status") == "paralysis":
            spd *= 0.5

        prio = move.get("priority", 0)
        actions_queue.append({
            "side": "player",
            "actor_idx": p_idx,
            "move": move,
            "target_idx": order.target_idx,
            "priority": prio,
            "speed": spd
        })

    # Ordens da IA
    for order in ai_orders:
        o_idx = order["pokemon_idx"]
        o_mon = opponent_team[o_idx]
        moves = o_mon.get("moves", [])
        move = moves[order["move_idx"]] if order["move_idx"] < len(moves) else MOVES_DATABASE["tackle"]

        spd = calculate_scaled_stats(o_mon.get("stats", []), o_mon.get("level", 5))["speed"]
        spd *= o_mon.get("stat_buffs", {}).get("speed", 1.0)
        if o_mon.get("status") == "paralysis":
            spd *= 0.5

        prio = move.get("priority", 0)
        actions_queue.append({
            "side": "opponent",
            "actor_idx": o_idx,
            "move": move,
            "target_idx": order["target_idx"],
            "priority": prio,
            "speed": spd
        })

    # Ordena todas as ações por Prioridade e depois Velocidade decrescente
    actions_queue.sort(key=lambda a: (a["priority"], a["speed"]), reverse=True)

    # 3. Execução das ações da rodada
    for act in actions_queue:
        side = act["side"]
        actor_idx = act["actor_idx"]
        move = act["move"]
        target_idx = act["target_idx"]

        attacker = player_team[actor_idx] if side == "player" else opponent_team[actor_idx]
        if attacker.get("current_hp", 0) <= 0:
            continue  # Pokémon foi nocauteado antes da sua vez

        enemy_team = opponent_team if side == "player" else player_team
        target_side = "opponent" if side == "player" else "player"
        actor_tag = f"Seu {attacker['name']} [{pos_names[actor_idx]}]" if side == "player" else f"{trainer_name} com {attacker['name']} [{pos_names[actor_idx]}]"

        step_logs = []

        def flush_step(kind, t_side=None, t_idx=None, is_aoe=False):
            steps.append({
                "logs": step_logs,
                "side": side,
                "actor_idx": actor_idx,
                "move_type": move.get("type", "normal"),
                "move_name": move.get("name", ""),
                "is_aoe": is_aoe,
                "kind": kind,
                "target_side": t_side,
                "target_idx": t_idx,
            })

        # Checagem de Sono
        if attacker.get("status") == "sleep":
            attacker["sleep_turns"] = attacker.get("sleep_turns", 2) - 1
            if attacker["sleep_turns"] <= 0:
                attacker["status"] = None
                step_logs.append(f"✨ {actor_tag} acordou!")
            else:
                step_logs.append(f"💤 {actor_tag} está dormindo e não pôde agir!")
                logs.extend(step_logs)
                flush_step("none")
                continue

        # Checagem de Paralisia
        if attacker.get("status") == "paralysis" and random.random() < 0.25:
            step_logs.append(f"⚡ {actor_tag} está paralisado e travou!")
            logs.extend(step_logs)
            flush_step("none")
            continue

        # Checagem de Precisão
        if random.random() * 100 > move.get("accuracy", 100):
            step_logs.append(f"💨 {actor_tag} usou {move['name']}, mas errou o alvo!")
            logs.extend(step_logs)
            flush_step("none")
            continue

        # Golpe Próprio (Buff / Heal)
        if move.get("target_type") == "self" or move.get("category") == "buff":
            if move.get("category") == "buff":
                b_stat = move.get("buff_stat", "attack")
                mult = move.get("buff_mult", 1.4)
                if "stat_buffs" not in attacker:
                    attacker["stat_buffs"] = {}
                attacker["stat_buffs"][b_stat] = attacker["stat_buffs"].get(b_stat, 1.0) * mult
                step_logs.append(f"💪 {actor_tag} usou {move['name']}! Seu {b_stat.upper()} aumentou!")
                logs.extend(step_logs)
                flush_step("buff", side, actor_idx)
            elif move.get("category") == "heal":
                heal = int(attacker["max_hp"] * move.get("heal_pct", 0.4))
                attacker["current_hp"] = min(attacker["max_hp"], attacker["current_hp"] + heal)
                step_logs.append(f"💚 {actor_tag} usou {move['name']} e recuperou {heal} HP! ({attacker['current_hp']}/{attacker['max_hp']})")
                logs.extend(step_logs)
                flush_step("heal", side, actor_idx)
            continue

        # Golpes Ofensivos e de Status
        target_list = []
        is_aoe = move.get("target_type") == "all_opponents"

        if is_aoe:
            target_list = [m for m in enemy_team if m.get("current_hp", 0) > 0]
            step_logs.append(f"🌊 {actor_tag} desferiu {move['name']} em ÁREA contra todos os oponentes!")
        else:
            # Alvo único com redirecionamento automático caso o alvo original tenha caído
            valid_targets = get_triple_valid_targets(actor_idx, enemy_team)
            if not valid_targets:
                continue
            if target_idx not in valid_targets or enemy_team[target_idx].get("current_hp", 0) <= 0:
                target_idx = valid_targets[0]  # Redireciona
            target_list = [enemy_team[target_idx]]

        step_kind = "status" if move.get("category") == "status" else "damage"

        for defender in target_list:
            if defender.get("current_hp", 0) <= 0:
                continue

            def_pos = next((i for i, m in enumerate(enemy_team) if m == defender), 0)
            def_tag = f"Seu {defender['name']} [{pos_names[def_pos]}]" if side != "player" else f"{defender['name']} do oponente [{pos_names[def_pos]}]"

            if move.get("category") == "status":
                st = move.get("status")
                if not defender.get("status"):
                    defender["status"] = st
                    if st == "sleep":
                        defender["sleep_turns"] = random.randint(1, 3)
                    status_names = {"paralysis": "⚡ Paralisado", "burn": "🔥 Queimado", "sleep": "💤 Adormecido", "poison": "☠️ Envenenado"}
                    step_logs.append(f"✨ {actor_tag} aplicou {move['name']} em {def_tag}! Ficou {status_names.get(st, st)}!")
                else:
                    step_logs.append(f"{actor_tag} tentou aplicar status, mas {def_tag} já tem uma condição!")
                target_idx = def_pos
                continue

            # Cálculo de Dano
            lvl = attacker.get("level", 5)
            atk_stat = calculate_scaled_stats(attacker.get("stats", []), lvl, attacker.get("bonus_stats", {}))["attack"]
            def_stat = calculate_scaled_stats(defender.get("stats", []), defender.get("level", 5), defender.get("bonus_stats", {}))["defense"]

            atk_val = atk_stat * attacker.get("stat_buffs", {}).get("attack", 1.0)
            def_val = def_stat * defender.get("stat_buffs", {}).get("defense", 1.0)

            if attacker.get("status") == "burn" and move.get("category") == "physical":
                atk_val *= 0.5

            m_type = move.get("type", "normal")
            type_mult = get_type_multiplier([m_type], defender.get("types", ["NORMAL"]))
            crit = 1.5 if random.random() < 0.10 else 1.0
            pwr = move.get("power", 40)
            aoe_modifier = 0.75 if is_aoe else 1.0

            base_dmg = (((2 * lvl / 5 + 2) * pwr * (atk_val / max(def_val, 1))) / 50) + 2
            dmg = max(1, int(base_dmg * type_mult * crit * aoe_modifier * random.uniform(0.88, 1.05)))

            eff_text = ""
            if type_mult >= 2.0:
                eff_text = " 💥 Super Efetivo!"
            elif type_mult <= 0.5 and type_mult > 0:
                eff_text = " 🛡️ Pouco efetivo..."
            elif type_mult == 0.0:
                eff_text = " ⛔ Não teve efeito!"

            crit_text = " ⚡ Golpe Crítico!" if crit > 1.0 else ""

            defender["current_hp"] = max(0, defender["current_hp"] - dmg)
            step_logs.append(f"⚔️ {actor_tag} atingiu {def_tag} com {move['name']} causando {dmg} de dano!{eff_text}{crit_text} ({defender['current_hp']}/{defender['max_hp']} HP)")

            # Efeito secundário de status
            if move.get("status") and not defender.get("status") and defender["current_hp"] > 0:
                if random.random() < move.get("status_chance", 0):
                    st = move["status"]
                    defender["status"] = st
                    if st == "sleep":
                        defender["sleep_turns"] = random.randint(1, 3)
                    status_names = {"paralysis": "⚡ Paralisado", "burn": "🔥 Queimado", "sleep": "💤 Adormecido", "poison": "☠️ Envenenado"}
                    step_logs.append(f"💥 Efeito secundário! {def_tag} ficou {status_names.get(st, st)}!")

            if defender["current_hp"] <= 0:
                step_logs.append(f"💀 {def_tag} foi nocauteado!")

            target_idx = def_pos

        logs.extend(step_logs)
        flush_step(step_kind, target_side, target_idx, is_aoe)

    # 4. Efeitos de Status no final da rodada para todos os Pokémon vivos
    tick_logs = []
    for side_team, side_prefix in [(player_team, "Seu"), (opponent_team, f"{trainer_name} com")]:
        for idx, mon in enumerate(side_team):
            if mon.get("current_hp", 0) > 0:
                tag = f"{side_prefix} {mon['name']} [{pos_names[idx]}]"
                if mon.get("status") == "burn":
                    b_dmg = max(1, int(mon["max_hp"] * 0.08))
                    mon["current_hp"] = max(0, mon["current_hp"] - b_dmg)
                    tick_logs.append(f"🔥 {tag} sofreu {b_dmg} de dano pela queimadura! ({mon['current_hp']}/{mon['max_hp']})")
                elif mon.get("status") == "poison":
                    p_dmg = max(1, int(mon["max_hp"] * 0.10))
                    mon["current_hp"] = max(0, mon["current_hp"] - p_dmg)
                    tick_logs.append(f"☠️ {tag} sofreu {p_dmg} de dano pelo veneno! ({mon['current_hp']}/{mon['max_hp']})")

    if tick_logs:
        logs.extend(tick_logs)
        steps.append({
            "logs": tick_logs,
            "side": None,
            "actor_idx": None,
            "move_type": None,
            "move_name": None,
            "is_aoe": False,
            "kind": "tick",
            "target_side": None,
            "target_idx": None,
        })

    # 5. Condições de Fim de Batalha Tripla
    player_wiped = all(m.get("current_hp", 0) <= 0 for m in player_team)
    opponent_wiped = all(m.get("current_hp", 0) <= 0 for m in opponent_team)

    is_finished = player_wiped or opponent_wiped
    winner = "player" if opponent_wiped else "opponent" if player_wiped else None
    xp_earned = 300 if winner == "player" else 100 if winner == "opponent" else 0
    coins_earned = 200 if winner == "player" else 60 if winner == "opponent" else 0

    return {
        "player_team": player_team,
        "opponent_team": opponent_team,
        "logs": logs,
        "steps": steps,
        "is_finished": is_finished,
        "winner": winner,
        "xp_earned": xp_earned,
        "coins_earned": coins_earned,
    }

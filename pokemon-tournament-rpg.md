# Plano de Projeto - RPG de Torneios Pokémon (Kanto)

**Status:** PLANEJAMENTO APROVADO PARA REVISÃO  
**Tipo de Projeto:** WEB (FastAPI + HTML5/CSS/JS SPA)  
**Agente Responsável:** `@project-planner`  
**Data:** 23/08/2026  

---

## 1. Visão Geral e Arquitetura

Transformar a aplicação Pokédex em um jogo RPG de Torneios Pokémon onde o treinador treina seu Pokémon inicial (Rank D), acumula XP em batalhas, evolui para novas formas e disputa torneios progressivos (Ranks D, C, B, A e S).

```
+-------------------------------------------------------------------------+
|                              INTERFACE SPA                              |
|   [📖 Pokédex & Ranks]  [🎒 Meu Treinador]  [🏋️ Dojo]  [🏆 Torneio]    |
+-------------------------------------------------------------------------+
                                    |
                    +---------------+---------------+
                    |                               |
          [FastAPI Backend]                [localStorage Engine]
   - /api/player/train (XP/EV)           - Estado do Treinador
   - /api/player/evolve (Evolução)       - Nível, XP, Moedas, Troféus
   - /api/tournament/match (Combate)     - Pokémon Ativo
   - /api/ranks (Dados dos 151)
```

---

## 2. Divisão de Tarefas (Task Breakdown)

### Tarefa 1: Motor de Combate e Lógica de RPG (Backend)
- **Agente:** `@backend-specialist`
- **Skills:** `@clean-code`, `@api-patterns`
- **Entrada:** Stats do atacante e defensor, multiplicadores de fraqueza/resistência, nível e bônus de treino.
- **Saída:** Endpoint `/api/tournament/match` que simula a rodada de combate com log de dano e determina o vencedor.
- **Verificação:** Script de teste simulando combate entre Bulbasaur e Charmander com validação de dano.

### Tarefa 2: Sistema de Progressão (XP, Treino e Evolução)
- **Agente:** `@backend-specialist`
- **Skills:** `@clean-code`, `@game-development`
- **Entrada:** Requisição de treino com moedas ou de evolução ao atingir nível 16/32.
- **Saída:** Endpoints `/api/player/train` e `/api/player/evolve` que atualizam atributos e estágio evolutivo.
- **Verificação:** Requisição de teste subindo de nível e evoluindo Bulbasaur -> Ivysaur -> Venusaur.

### Tarefa 3: Interface do Treinador & Arena de Torneio (Frontend)
- **Agente:** `@frontend-specialist`
- **Skills:** `@frontend-design`, `@web-design-guidelines`
- **Entrada:** Dados do jogador e chaves de torneio.
- **Saída:** Abas no [index.html](file:///c:/Users/User%20Yooga/Documents/PROJETOS/pokemon/templates/index.html) contendo:
  1. *Meu Pokémon* (card interativo com barra de XP animada e botão de Evoluir).
  2. *Dojo de Treino* (botões de treino de Ataque, Defesa e Velocidade com gasto de moedas).
  3. *Arena de Torneio* (chaveamento visual de 8 treinadores e arena de batalha animada com logs de combate).
- **Verificação:** Executar no navegador e completar um ciclo completo de jogo (Escolha -> Treino -> Evolução -> Vitória no Torneio).

---

## 3. Critérios de Sucesso
- [ ] O jogador pode escolher seu Pokémon inicial (Rank D).
- [ ] Ganho de XP e subida de nível funcional com aumento perceptível de poder.
- [ ] Evolução funcional ao atingir os marcos de nível (ex: Nível 16 e 32).
- [ ] Chaveamento de torneio de 8 participantes com IA por Rank.
- [ ] Vencer o torneio concede troféu e moedas para continuar a jornada.

# 🏟️ Pokémon Stadium Kanto: Batalha Tripla (3v3) & Pokédex Oficial

Um jogo RPG tático de combate Pokémon inspirado em **Pokémon Stadium** e **Pokémon Black & White**, desenvolvido com **FastAPI (Python)** no backend e **Phaser.js 3 (WebGL)** + Vanilla CSS no frontend.

---

## 🌟 Funcionalidades Principais

### 1. ⚔️ Arena Stadium 3v3 Simultânea (Phaser.js 3 WebGL)
* **Combate 3 vs 3 no Campo:** Os 3 Pokémon do jogador e os 3 Pokémon do oponente lutam juntos no estádio simultaneamente.
* **Regras de Alcance Tático (*Range*):**
  * `[👈 Esquerda]`: Alcança os oponentes da Esquerda e do Centro.
  * `[🎯 Centro]`: Alcance total sobre todos os 3 oponentes (Capitão).
  * `[👉 Direita]`: Alcança os oponentes da Direita e do Centro.
* **Sistema de Partículas Elementais (VFX):**
  * 🔥 **Fogo:** Projéteis incandescentes e explosão de chamas (*Brasas*, *Lança-Chamas*).
  * 💧 **Água:** Esferas pressurizadas e ondas cortando o estádio (*Jato de Água*, *Surfar*).
  * ⚡ **Elétrico:** Raios verticais caindo do céu com *Screen Flash* (*Choque do Trovão*, *Raio*).
  * 🍃 **Planta:** Ciclones de folhas cortantes (*Chicote de Vinha*, *Folha Navalha*).
  * 🪨 **Pedra / Terra:** Rochas caindo com **Tremores de Câmera (*Screen Shake*)** (*Terremoto*, *Deslize de Pedras*).
  * 💥 **Físico:** Faíscas de impacto com dash de ataque (*Investida*, *Ataque Rápido*).
* **Animações de Nocaute:** Pokémon derrotado afunda suavemente no gramado com fade-out.

---

### 2. 🎯 Moveset de 4 Golpes Reais & Efeitos de Status
Cada Pokémon possui um moveset balanceado composto por:
1. **Golpe Básico/Rápido:** Alta velocidade e precisão (*Investida*, *Ataque Rápido* com prioridade).
2. **STAB Primário:** Golpe com bônus elemental do tipo do Pokémon (*Brasas*, *Jato de Água*, *Chicote de Vinha*, etc.).
3. **Golpe de Cobertura:** Para surpreender tipos desfavoráveis (*Mordida*, *Cauda de Ferro*, *Cacos de Gelo*).
4. **Golpe Tático / Status / Buff:** *Dança das Espadas* (+40% Atk), *Defesa de Ferro* (+40% Def), *Agilidade* (+50% Spd), *Recuperar* (cura 40% HP).
* **Efeitos de Status Ativos:**
  * ⚡ **`PAR` (Paralisia):** -50% de velocidade e 25% de chance de travar turno.
  * 🔥 **`BRN` (Queimadura):** -50% de dano físico e dano contínuo a cada rodada.
  * 💤 **`SLP` (Sono):** Incapacitado por 1 a 3 turnos.
  * ☠️ **`PSN` (Veneno):** 10% de dano de HP a cada rodada.

---

### 3. 🥋 Dojo de Kanto & RPG Progressivo
* **Evolução de Estágio:** Evolua seus Pokémon na linha evolutiva oficial (ex: Bulbasaur ➔ Ivysaur ➔ Venusaur) ao atingir o nível necessário.
* **Treino no Dojo:** Invista PokéMoedas ganhas em torneios para aumentar atributos específicos (+3 Atk, Def, Spd ou HP) e ganhar XP extra.
* **Fórmula Oficial de RPG:** Stats e vida balanceados com base nas fórmulas da *Game Freak*, escalando do Nível 5 ao 50.

---

### 4. 🏆 Torneios por Ranks (D, C, B, A, S)
* Chave de torneio estruturada: **Quartas de Final**, **Semifinal** e **Grande Final**.
* Enfrente treinadores icônicos de Kanto (Gary, Brock, Misty, Lt. Surge, Blaine, Giovanni, Lance) com equipes temáticas adaptadas para batalhas triplas.

---

### 5. 🎮 Modos de Jogo & Tema Retrô Game Boy
* **🟢 Modo Fácil:** Escolha livremente seus 3 Pokémon iniciais favoritos de Rank D.
* **🔴 Modo Difícil:** Receba 3 Pokémon de Rank D sorteados aleatoriamente.
* **🎮 Modo DMG (Game Boy Retrô):** Alterne a qualquer momento para o visual monocromático clássico de 4 tons de verde com fonte pixelada *Press Start 2P*.

---

### 6. 📖 Pokédex Oficial de Kanto (`/pokedex`)
* Página independente com os **151 Pokémon originais de Kanto**.
* Filtros rápidos por Rank (S, A, B, C, D).
* **3 Modos de Visualização:** Pixel Clássico, GIF Animado e HD Oficial.
* **Áudio Oficial:** Ouça o grito (*Cry*) original de cada Pokémon.
* Detalhes completos com Stats Base, Fraquezas e Linha Evolutiva interativa.

---

## 🛠️ Tecnologias Utilizadas

* **Backend:** [Python 3.10+](https://www.python.org/) • [FastAPI](https://fastapi.tiangolo.com/) • [Uvicorn](https://www.uvicorn.org/) • [PokeAPI GraphQL (v2)](https://pokeapi.co/)
* **Frontend:** HTML5 Semântico • Vanilla CSS Moderno • JavaScript ES6+ • [Phaser.js 3 (WebGL)](https://phaser.io/)

---

## 🚀 Como Executar o Projeto

### 1. Pré-requisitos
Certifique-se de ter o Python 3.10 ou superior instalado no seu sistema.

### 2. Instalação das Dependências
No terminal, dentro da pasta do projeto, execute:
```bash
pip install fastapi uvicorn requests
```

### 3. Iniciar o Servidor
Execute o servidor com recarregamento automático:
```bash
python -m uvicorn main:app --reload
```

### 4. Acessar as Rotas no Navegador
* 🎮 **Jogo Pokémon Stadium (3v3):** [http://localhost:8000/](http://localhost:8000/)
* 📖 **Pokédex Oficial (151):** [http://localhost:8000/pokedex](http://localhost:8000/pokedex)
* 📑 **Documentação da API (Swagger):** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 📂 Estrutura de Arquivos

```
pokemon/
├── main.py                    # Servidor FastAPI, endpoints de torneio, treino, evolução e cálculo 3v3
├── templates/
│   ├── index.html             # Interface do jogo com Arena Stadium (Phaser.js), Dojo e Torneios
│   └── pokedex.html           # Pokédex independente dos 151 Pokémon com áudio e filtros
├── GAME_FEATURES_ROADMAP.md   # Roadmap de arquitetura e futuras expansões do jogo
└── README.md                  # Documentação do projeto
```

---

## 📜 Licença
Projeto criado para fins educacionais e de entretenimento. Pokémon e todos os nomes e imagens de personagens são marcas registradas da Nintendo, Game Freak e Creatures Inc.

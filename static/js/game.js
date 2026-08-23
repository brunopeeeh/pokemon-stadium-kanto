const POS_LABELS = ["👈 Esquerda", "🎯 Centro", "👉 Direita"];

const TYPE_COLORS = {
    normal: '#A8A77A', fire: '#EE8130', water: '#6390F0', electric: '#F7D02C',
    grass: '#7AC74C', ice: '#96D9D6', fighting: '#C22E28', poison: '#A33EA1',
    ground: '#E2BF65', flying: '#A98FF3', psychic: '#F95587', bug: '#A6B91A',
    rock: '#B6A136', ghost: '#735797', dragon: '#6F35FC', steel: '#B7B7CE', fairy: '#D685AD'
};

// ================= SINTETIZADOR DE ÁUDIO WEB AUDIO API =================
const SoundEngine = {
    ctx: null,
    enabled: true,

    init() {
        if (!this.ctx && (window.AudioContext || window.webkitAudioContext)) {
            this.ctx = new (window.AudioContext || window.webkitAudioContext)();
        }
    },

    playTone(freq, type, duration, gainVal = 0.1) {
        if (!this.enabled) return;
        this.init();
        if (!this.ctx) return;

        try {
            const osc = this.ctx.createOscillator();
            const gain = this.ctx.createGain();
            osc.type = type;
            osc.frequency.setValueAtTime(freq, this.ctx.currentTime);

            gain.gain.setValueAtTime(gainVal, this.ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.0001, this.ctx.currentTime + duration);

            osc.connect(gain);
            gain.connect(this.ctx.destination);

            osc.start();
            osc.stop(this.ctx.currentTime + duration);
        } catch (e) {
            // AudioContext policy handled
        }
    },

    click() {
        this.playTone(600, 'sine', 0.06, 0.05);
    },

    selectMove() {
        this.playTone(880, 'triangle', 0.09, 0.08);
    },

    attackPhysical() {
        this.playTone(120, 'square', 0.15, 0.15);
    },

    attackFire() {
        this.playTone(220, 'sawtooth', 0.25, 0.12);
    },

    attackWater() {
        this.playTone(400, 'sine', 0.22, 0.12);
    },

    attackThunder() {
        this.playTone(950, 'sawtooth', 0.18, 0.15);
    },

    attackRock() {
        this.playTone(80, 'square', 0.3, 0.2);
    },

    victory() {
        if (!this.enabled) return;
        [523.25, 659.25, 783.99, 1046.50].forEach((freq, i) => {
            setTimeout(() => this.playTone(freq, 'triangle', 0.25, 0.12), i * 140);
        });
    },

    defeat() {
        if (!this.enabled) return;
        [400, 350, 300, 220].forEach((freq, i) => {
            setTimeout(() => this.playTone(freq, 'sawtooth', 0.25, 0.12), i * 160);
        });
    }
};

let gameState = {
    mode: 'easy',
    coins: 150,
    team: [],
};

let rankDPool = [];
let selectedStarterIds = [];
let selectedDojoMemberIndex = 0;

let currentTournamentTier = 'D';
let tournamentOpponents = [];
let currentMatchIndex = 0;

// Estado da Batalha Stadium
let stadiumBattle = {
    inBattle: false,
    playerTeam: [],
    oppTeam: [],
    oppTrainerName: "",
    orders: [
        { pokemon_idx: 0, move_idx: 0, target_idx: 0 },
        { pokemon_idx: 1, move_idx: 0, target_idx: 1 },
        { pokemon_idx: 2, move_idx: 0, target_idx: 2 },
    ]
};

let phaserGame = null;
let stadiumScene = null;

// Abas
const tabBtns = document.querySelectorAll('.tab-btn');
tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        SoundEngine.click();
        tabBtns.forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        btn.classList.add('active');
        document.getElementById(`tab-${btn.dataset.tab}`).classList.add('active');
    });
});

// Tema Retro
document.getElementById('btn-toggle-retro').addEventListener('click', () => {
    SoundEngine.click();
    document.body.classList.toggle('retro-mode');
    const isRetro = document.body.classList.contains('retro-mode');
    document.getElementById('btn-toggle-retro').innerText = isRetro ? '✨ Moderno' : '🎮 DMG';
});

// Toggle Som
const btnSound = document.getElementById('btn-toggle-sound');
if (btnSound) {
    btnSound.addEventListener('click', () => {
        SoundEngine.enabled = !SoundEngine.enabled;
        btnSound.innerText = SoundEngine.enabled ? '🔊 Som: ON' : '🔇 Som: OFF';
        if (SoundEngine.enabled) SoundEngine.click();
    });
}

function saveGame() {
    localStorage.setItem('kanto_stadium_rpg', JSON.stringify(gameState));
    document.getElementById('player-coins').innerText = gameState.coins;
}

function loadGame() {
    const saved = localStorage.getItem('kanto_stadium_rpg');
    if (saved) {
        try {
            gameState = JSON.parse(saved);
            updateUI();
        } catch (e) {
            showNewGameModal();
        }
    } else {
        showNewGameModal();
    }
}

function showNewGameModal() {
    document.getElementById('easy-selection-area').style.display = 'none';
    document.getElementById('new-game-modal').style.display = 'flex';
}

async function fetchRankDPool() {
    const res = await fetch('/api/ranks');
    const data = await res.json();
    rankDPool = data.ranks['D'] || [];
}

async function startEasyModeFlow() {
    SoundEngine.click();
    gameState.mode = 'easy';
    selectedStarterIds = [];
    document.getElementById('easy-selection-area').style.display = 'block';

    const poolGrid = document.getElementById('starter-pool-grid');
    poolGrid.innerHTML = rankDPool.map(mon => `
        <div class="starter-item" data-id="${mon.id}" onclick="toggleStarterSelect(${mon.id})">
            <img src="https://raw.githubusercontent.com/msikma/pokesprite/master/pokemon-gen8/regular/${mon.name.toLowerCase()}.png" alt="${mon.name}">
            <span>${mon.name.charAt(0).toUpperCase() + mon.name.slice(1)}</span>
        </div>
    `).join('');

    updateSelectionCounter();
}

function toggleStarterSelect(id) {
    SoundEngine.click();
    const idx = selectedStarterIds.indexOf(id);
    if (idx >= 0) {
        selectedStarterIds.splice(idx, 1);
    } else {
        if (selectedStarterIds.length < 3) {
            selectedStarterIds.push(id);
        }
    }

    document.querySelectorAll('.starter-item').forEach(el => {
        const monId = parseInt(el.dataset.id, 10);
        el.classList.toggle('selected', selectedStarterIds.includes(monId));
    });

    updateSelectionCounter();
}

function updateSelectionCounter() {
    const count = selectedStarterIds.length;
    document.getElementById('selection-counter').innerText = `${count}/3 Escolhidos`;
    document.getElementById('btn-confirm-team').disabled = count !== 3;
}

async function fetchTeamRoster(ids) {
    const team = [];
    for (let id of ids) {
        const res = await fetch(`/api/pokemon/${id}`);
        if (!res.ok) throw new Error(`Falha ao buscar Pokémon #${id}`);
        const data = await res.json();
        team.push({
            data: data,
            level: 5,
            xp: 0,
            bonusStats: { attack: 0, defense: 0, speed: 0, hp: 0 }
        });
    }
    return team;
}

async function confirmEasyTeam() {
    SoundEngine.click();
    document.getElementById('new-game-modal').style.display = 'none';
    try {
        gameState.team = await fetchTeamRoster(selectedStarterIds);
    } catch (err) {
        console.error("Erro ao montar time:", err);
        showNewGameModal();
        return;
    }
    gameState.coins = 150;
    saveGame();
    updateUI();
}

async function startHardModeFlow() {
    SoundEngine.click();
    gameState.mode = 'hard';
    document.getElementById('new-game-modal').style.display = 'none';

    const shuffled = [...rankDPool].sort(() => 0.5 - Math.random());
    const random3 = shuffled.slice(0, 3);

    try {
        gameState.team = await fetchTeamRoster(random3.map(m => m.id));
    } catch (err) {
        console.error("Erro ao sortear time:", err);
        showNewGameModal();
        return;
    }
    gameState.coins = 150;
    saveGame();
    updateUI();
    alert(`🎲 [Modo Difícil] Sua equipe sorteada é: ${gameState.team.map(m => m.data.name).join(', ')}!`);
}

function updateUI() {
    document.getElementById('player-coins').innerText = gameState.coins;
    const modePill = document.getElementById('display-mode-pill');
    if (gameState.mode === 'hard') {
        modePill.className = 'mode-pill hard';
        modePill.innerText = '🔴 Difícil';
    } else {
        modePill.className = 'mode-pill easy';
        modePill.innerText = '🟢 Fácil';
    }

    renderTeamSlots();
    renderDojoMemberSelector();
    loadTournamentBracket();
}

function renderTeamSlots() {
    const container = document.getElementById('team-container');
    if (!gameState.team || gameState.team.length === 0) return;

    let html = '';
    gameState.team.forEach((member, index) => {
        const p = member.data;
        const xpNeeded = member.level * 100;
        const xpPct = Math.min((member.xp / xpNeeded) * 100, 100);

        const statVal = name => p.stats.find(s => s.name.toLowerCase() === name)?.val || 45;
        const atkBase = Math.max(statVal('attack'), statVal('special attack'));
        const defBase = Math.max(statVal('defense'), statVal('special defense'));

        const hp = Math.round((2 * statVal('hp') * member.level) / 100 + member.level + 10 + (member.bonusStats.hp || 0) * 2);
        const atk = Math.round((2 * atkBase * member.level) / 100 + 5 + (member.bonusStats.attack || 0));
        const def = Math.round((2 * defBase * member.level) / 100 + 5 + (member.bonusStats.defense || 0));
        const spd = Math.round((2 * statVal('speed') * member.level) / 100 + 5 + (member.bonusStats.speed || 0));

        let evolveBtnHTML = '';
        if (p.evolution_chain && p.evolution_chain.length > 1) {
            const currentIdx = p.evolution_chain.findIndex(e => e.id === p.id);
            if (currentIdx >= 0 && currentIdx < p.evolution_chain.length - 1) {
                const nextEvo = p.evolution_chain[currentIdx + 1];
                const reqLevel = currentIdx === 0 ? 16 : 32;
                if (member.level >= reqLevel) {
                    evolveBtnHTML = `
                        <button class="btn-evolve-slot" onclick="executeEvolveMember(${index}, ${nextEvo.id})">
                            ✨ Evoluir para ${nextEvo.name}! (Nv. ${member.level}/${reqLevel})
                        </button>
                    `;
                }
            }
        }

        html += `
            <div class="team-slot">
                <div class="slot-header">
                    <div class="slot-sprite-box">
                        <span class="slot-pos-tag">${POS_LABELS[index]}</span>
                        <img src="${p.sprite}" alt="${p.name}" class="slot-sprite">
                        <span class="slot-level-badge">Nv. ${member.level}</span>
                    </div>
                    <div class="slot-details">
                        <div class="slot-title">
                            <h4>#${String(p.id).padStart(3, '0')} ${p.name}</h4>
                            <span class="badge" style="background:${p.rank_info?.badge_bg || '#666'}; color:#111; font-weight:800; font-size:0.62rem; padding: 2px 6px; border-radius: 4px;">
                                ${p.rank_info?.name || p.rank}
                            </span>
                        </div>
                        <div style="display:flex; gap:4px; margin-top:3px;">
                            ${p.types.map(t => `<span class="badge" style="background:${TYPE_COLORS[t.toLowerCase()] || '#777'}; font-size:0.58rem; padding:1px 5px; color:#111; font-weight:bold; border-radius:3px;">${t}</span>`).join('')}
                        </div>
                        <div class="slot-xp-bar-bg">
                            <div class="slot-xp-bar-fill" style="width: ${xpPct}%;"></div>
                        </div>
                    </div>
                </div>
                <div class="slot-stat-meters">
                    <div class="stat-item"><span>❤️ HP</span><strong>${hp}</strong></div>
                    <div class="stat-item"><span>⚔️ Atk</span><strong>${atk}</strong></div>
                    <div class="stat-item"><span>🛡️ Def</span><strong>${def}</strong></div>
                    <div class="stat-item"><span>⚡ Spd</span><strong>${spd}</strong></div>
                </div>
                ${evolveBtnHTML}
            </div>
        `;
    });

    container.innerHTML = html;
}

// Treino
function renderDojoMemberSelector() {
    const sel = document.getElementById('dojo-member-selector');
    if (!gameState.team || gameState.team.length === 0) return;

    sel.innerHTML = gameState.team.map((m, idx) => `
        <div class="member-select-btn ${idx === selectedDojoMemberIndex ? 'active' : ''}" onclick="selectDojoMember(${idx})">
            <img src="${m.data.sprite}" alt="${m.data.name}">
            <span style="font-size:0.75rem;">${m.data.name}</span>
            <small style="color:var(--cyan); font-weight:bold;">Nv. ${m.level}</small>
        </div>
    `).join('');
}

function selectDojoMember(idx) {
    SoundEngine.click();
    selectedDojoMemberIndex = idx;
    renderDojoMemberSelector();
}

async function executeTrain(statKey) {
    SoundEngine.click();
    if (gameState.coins < 50) {
        alert("PokéMoedas insuficientes! Vença lutas de torneio para ganhar mais.");
        return;
    }

    const member = gameState.team[selectedDojoMemberIndex];
    try {
        const res = await fetch('/api/player/train', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                pokemon_id: member.data.id,
                current_level: member.level,
                current_xp: member.xp,
                train_type: statKey,
                bonus_stats: member.bonusStats,
                coins: gameState.coins
            })
        });
        const data = await res.json();
        if (data.success) {
            SoundEngine.victory();
            member.level = data.level;
            member.xp = data.xp;
            member.bonusStats = data.bonus_stats;
            gameState.coins = data.coins;
            saveGame();
            updateUI();
            if (data.leveled_up) alert(`🎉 Seu ${member.data.name} subiu para o Nível ${data.level}!`);
        }
    } catch (err) {
        console.error("Erro no treino:", err);
    }
}

async function executeEvolveMember(teamIndex, targetId) {
    SoundEngine.victory();
    const member = gameState.team[teamIndex];
    try {
        const res = await fetch('/api/player/evolve', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                current_id: member.data.id,
                target_id: targetId,
                level: member.level,
                bonus_stats: member.bonusStats
            })
        });
        const data = await res.json();
        if (data.success) {
            member.data = data.pokemon;
            saveGame();
            updateUI();
            alert(data.message);
        }
    } catch (err) {
        console.error("Erro ao evoluir:", err);
    }
}

// ================= TORNEIO =================
const tierTabs = document.querySelectorAll('.tier-tab');
tierTabs.forEach(tab => {
    tab.addEventListener('click', () => {
        SoundEngine.click();
        tierTabs.forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        currentTournamentTier = tab.dataset.tier;
        loadTournamentBracket();
    });
});

async function loadTournamentBracket() {
    try {
        const avgLevel = gameState.team.length > 0 ? Math.round(gameState.team.reduce((a, b) => a + b.level, 0) / gameState.team.length) : 5;
        const res = await fetch('/api/tournament/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tier: currentTournamentTier, player_level: avgLevel })
        });
        const data = await res.json();
        tournamentOpponents = data.opponents;
        currentMatchIndex = 0;

        document.getElementById('tournament-tier-title').innerText = `Torneio ${data.tier_info.name} (Pokémon Stadium 3v3)`;
        renderBracket();
    } catch (err) {
        console.error("Erro ao carregar torneio:", err);
    }
}

function renderBracket() {
    const tree = document.getElementById('bracket-tree');
    if (!tournamentOpponents || tournamentOpponents.length === 0) return;

    const rounds = ["Quartas de Final (Rodada 1)", "Semifinal (Rodada 2)", "Grande Final (Rodada 3)"];
    let html = '';
    for (let i = 0; i < 3; i++) {
        const opp = tournamentOpponents[i] || { trainer_name: "Campeão", pokemon: { name: "Desconhecido" }, level: 20 };
        const isCurrent = i === currentMatchIndex;
        const isDone = i < currentMatchIndex;
        html += `
            <div class="bracket-match ${isCurrent ? 'current' : ''}">
                <div>
                    <strong>${rounds[i]}</strong><br>
                    <small style="color:var(--text-muted);">${isDone ? '✅ Vencida' : `${opp.trainer_name} (3 Pokémon Nv. ${opp.level})`}</small>
                </div>
                <span style="font-weight:800; font-size:0.75rem; color:${isCurrent ? 'var(--cyan)' : isDone ? 'var(--green)' : 'inherit'};">
                    ${isCurrent ? '⚔️ PRÓXIMO' : isDone ? '🏆 VITÓRIA' : '🔒'}
                </span>
            </div>
        `;
    }
    tree.innerHTML = html;
}

// ================= CENA PHASER 3: POKÉMON STADIUM HD WIDESCREEN =================
class StadiumScene extends Phaser.Scene {
    constructor() {
        super({ key: 'StadiumScene' });
        this.monSprites = { player: [], opp: [] };
        this.hpBars = { player: [], opp: [] };
        this.shadows = { player: [], opp: [] };
        this.pedestals = { player: [], opp: [] };
        this.posCoords = {
            opp: [ { x: 180, y: 90 }, { x: 400, y: 70 }, { x: 620, y: 90 } ],
            player: [ { x: 180, y: 260 }, { x: 400, y: 280 }, { x: 620, y: 260 } ]
        };
    }

    create() {
        stadiumScene = this;
        const { width, height } = this.cameras.main;

        // 1. Fundo do Estádio com Degradê Profundo
        const bg = this.add.graphics();
        bg.fillGradientStyle(0x0a1124, 0x0a1124, 0x03050c, 0x03050c, 1);
        bg.fillRect(0, 0, width, height);

        // 2. Plataforma de Gramado 3D Stadium (Oval)
        bg.fillStyle(0x0f3818, 1);
        bg.fillEllipse(width / 2, height / 2 + 5, width - 40, height - 50);

        // Textura de Faixas de Grama Concéntricas
        bg.fillStyle(0x154a20, 0.4);
        bg.fillEllipse(width / 2, height / 2 + 5, (width - 40) * 0.75, (height - 50) * 0.75);

        // Anel Neon Externo do Estádio
        bg.lineStyle(3.5, 0x00f0ff, 0.85);
        bg.strokeEllipse(width / 2, height / 2 + 5, width - 40, height - 50);

        // Borda Dourada Interna de Prestígio
        bg.lineStyle(2, 0xffd700, 0.5);
        bg.strokeEllipse(width / 2, height / 2 + 5, (width - 40) * 0.82, (height - 50) * 0.82);

        // Linha Central do Campo
        bg.lineStyle(1.5, 0xffffff, 0.3);
        bg.lineBetween(50, height / 2 + 5, width - 50, height / 2 + 5);

        // 3. Emblema da Pokébola Gigante no Centro da Arena
        this.drawCenterPokeball(width / 2, height / 2 + 5);

        // 4. Holofotes Dinâmicos e Flashes de Câmera da Torcida
        this.addStadiumSpotlights();
        this.addCrowdFlashbulbs();

        // Textura Fallback
        if (!this.textures.exists('mon_placeholder')) {
            const canvas = this.textures.createCanvas('mon_placeholder', 72, 72);
            if (canvas && canvas.context) {
                canvas.context.fillStyle = 'rgba(0,0,0,0)';
                canvas.context.fillRect(0, 0, 72, 72);
                canvas.refresh();
            }
        }

        if (stadiumBattle.inBattle) {
            this.initFighters();
        }
    }

    drawCenterPokeball(cx, cy) {
        const p = this.add.graphics();
        p.fillStyle(0x1b1b2f, 0.6);
        p.fillCircle(cx, cy, 46);

        p.fillStyle(0xd32f2f, 0.7);
        p.slice(cx, cy, 44, Phaser.Math.DegToRad(180), Phaser.Math.DegToRad(360), false);
        p.fillPath();

        p.fillStyle(0xe0e0e0, 0.7);
        p.slice(cx, cy, 44, Phaser.Math.DegToRad(0), Phaser.Math.DegToRad(180), false);
        p.fillPath();

        p.lineStyle(4, 0x111118, 1);
        p.lineBetween(cx - 44, cy, cx + 44, cy);
        p.strokeCircle(cx, cy, 44);

        p.fillStyle(0x111118, 1);
        p.fillCircle(cx, cy, 13);
        p.fillStyle(0x00f0ff, 0.95);
        p.fillCircle(cx, cy, 7);
    }

    addStadiumSpotlights() {
        const { width } = this.cameras.main;
        [80, width - 80].forEach(x => {
            const light = this.add.graphics();
            light.fillStyle(0xffffff, 0.09);
            light.fillTriangle(x, 10, x - 130, 360, x + 130, 360);

            this.tweens.add({
                targets: light,
                alpha: { from: 0.04, to: 0.14 },
                duration: 2400 + Math.random() * 1000,
                yoyo: true,
                repeat: -1,
                ease: 'Sine.easeInOut'
            });
        });
    }

    addCrowdFlashbulbs() {
        const { width, height } = this.cameras.main;
        this.time.addEvent({
            delay: 220,
            callback: () => {
                const flashX = Phaser.Math.Between(40, width - 40);
                const flashY = Phaser.Math.Between(15, 60);
                const flash = this.add.circle(flashX, flashY, Phaser.Math.Between(2, 4), 0xffffff, 0.9);
                this.tweens.add({
                    targets: flash,
                    scale: 2,
                    alpha: 0,
                    duration: 160,
                    onComplete: () => flash.destroy()
                });
            },
            loop: true
        });
    }

    initFighters() {
        this.clearFighters();

        // 3 Oponentes (Plataformas Vermelhas/Douradas)
        stadiumBattle.oppTeam.forEach((m, idx) => {
            const coord = this.posCoords.opp[idx];
            const isCaptain = idx === 1;
            const padColor = isCaptain ? 0xffd700 : 0xff3366;

            // 1. Pedestal Holográfico 3D
            const ped = this.add.graphics();
            ped.fillStyle(padColor, 0.15);
            ped.fillEllipse(coord.x, coord.y + 30, 66, 20);
            ped.lineStyle(2, padColor, 0.8);
            ped.strokeEllipse(coord.x, coord.y + 30, 66, 20);
            this.pedestals.opp[idx] = ped;

            // 2. Sombra de Contato
            const shadow = this.add.ellipse(coord.x, coord.y + 30, 46, 12, 0x000000, 0.55);
            this.shadows.opp[idx] = shadow;

            // 3. Sprite do Pokémon
            const texKey = this.textures.exists(`opp_${idx}`) ? `opp_${idx}` : 'mon_placeholder';
            const spr = this.add.image(coord.x, coord.y, texKey).setDisplaySize(72, 72);
            this.monSprites.opp[idx] = spr;

            // Idle Breathing
            this.tweens.add({
                targets: spr,
                y: coord.y - 4,
                duration: 1200 + idx * 200,
                yoyo: true,
                repeat: -1,
                ease: 'Sine.easeInOut'
            });

            // 4. Placa de HP Stadium HD
            const hpBar = this.createHPBar(coord.x, coord.y - 44, m.current_hp, m.max_hp, m.name, m.level, m.types);
            this.hpBars.opp[idx] = hpBar;

            if (m.current_hp <= 0) {
                spr.setAlpha(0.2).setTint(0x444444);
                shadow.setAlpha(0);
                ped.setAlpha(0.1);
            }
        });

        // 3 Jogador (Plataformas Ciano/Douradas)
        stadiumBattle.playerTeam.forEach((m, idx) => {
            const coord = this.posCoords.player[idx];
            const isCaptain = idx === 1;
            const padColor = isCaptain ? 0xffd700 : 0x00f0ff;

            // 1. Pedestal Holográfico 3D
            const ped = this.add.graphics();
            ped.fillStyle(padColor, 0.15);
            ped.fillEllipse(coord.x, coord.y + 30, 66, 20);
            ped.lineStyle(2, padColor, 0.8);
            ped.strokeEllipse(coord.x, coord.y + 30, 66, 20);
            this.pedestals.player[idx] = ped;

            // 2. Sombra
            const shadow = this.add.ellipse(coord.x, coord.y + 30, 46, 12, 0x000000, 0.55);
            this.shadows.player[idx] = shadow;

            // 3. Sprite do Pokémon
            const texKey = this.textures.exists(`p_${idx}`) ? `p_${idx}` : 'mon_placeholder';
            const spr = this.add.image(coord.x, coord.y, texKey).setDisplaySize(72, 72);
            this.monSprites.player[idx] = spr;

            // Idle Breathing
            this.tweens.add({
                targets: spr,
                y: coord.y - 4,
                duration: 1300 + idx * 150,
                yoyo: true,
                repeat: -1,
                ease: 'Sine.easeInOut'
            });

            // 4. Placa de HP Stadium HD
            const hpBar = this.createHPBar(coord.x, coord.y + 44, m.current_hp, m.max_hp, m.name, m.level, m.types);
            this.hpBars.player[idx] = hpBar;

            if (m.current_hp <= 0) {
                spr.setAlpha(0.2).setTint(0x444444);
                shadow.setAlpha(0);
                ped.setAlpha(0.1);
            }
        });
    }

    createHPBar(x, y, current, max, name, level, types) {
        const container = this.add.container(x, y);
        
        // Fundo da Placa HD
        const bg = this.add.rectangle(0, 0, 104, 18, 0x090a14, 0.9).setStrokeStyle(1.5, 0x223355);
        
        // Barra de Vida
        const pct = Math.max(0, current / max);
        const fillWidth = Math.max(0, 98 * pct);
        const color = pct <= 0.2 ? 0xff3366 : pct <= 0.5 ? 0xffd700 : 0x39ff14;
        const barBg = this.add.rectangle(0, 4, 98, 5, 0x111122);
        const bar = this.add.rectangle(-49 + fillWidth / 2, 4, fillWidth, 5, color);

        // Texto do Nome e Nível
        const label = this.add.text(-47, -7, `${name}`, {
            fontSize: '9.5px',
            fontFamily: 'Outfit, sans-serif',
            fontStyle: 'bold',
            color: '#ffffff',
            stroke: '#000000',
            strokeThickness: 2
        });

        const lvlLabel = this.add.text(47, -7, `Lv.${level || 5}`, {
            fontSize: '8.5px',
            fontFamily: 'Outfit, sans-serif',
            fontStyle: 'bold',
            color: '#00f0ff',
            stroke: '#000000',
            strokeThickness: 2
        }).setOrigin(1, 0);

        container.add([bg, barBg, bar, label, lvlLabel]);
        return { container, bar, label, lvlLabel };
    }

    updateHPBar(side, idx, current, max) {
        const hpObj = this.hpBars[side][idx];
        if (!hpObj) return;
        const pct = Math.max(0, current / max);
        const fillWidth = Math.max(0, 98 * pct);
        const color = pct <= 0.2 ? 0xff3366 : pct <= 0.5 ? 0xffd700 : 0x39ff14;

        hpObj.bar.fillColor = color;
        this.tweens.add({
            targets: hpObj.bar,
            width: fillWidth,
            x: -49 + fillWidth / 2,
            duration: 300
        });
    }

    clearFighters() {
        ['player', 'opp'].forEach(side => {
            this.monSprites[side].forEach(s => { if (s) s.destroy(); });
            this.shadows[side].forEach(sh => { if (sh) sh.destroy(); });
            this.pedestals[side].forEach(p => { if (p) p.destroy(); });
            this.hpBars[side].forEach(h => { if (h && h.container) h.container.destroy(); });
            this.monSprites[side] = [];
            this.shadows[side] = [];
            this.pedestals[side] = [];
            this.hpBars[side] = [];
        });
    }

    playAttackVFX(side, actorIdx, targetSide, targetIdx, moveName, isAoE, callback) {
        const actorSpr = this.monSprites[side][actorIdx];
        const targetCoord = isAoE ? { x: 400, y: targetSide === 'opp' ? 90 : 260 } : this.posCoords[targetSide][targetIdx];

        if (!actorSpr) { if (callback) callback(); return; }

        const origY = actorSpr.y;
        const dashY = side === 'player' ? origY - 26 : origY + 26;

        // Dash de Ataque
        this.tweens.add({
            targets: actorSpr,
            y: dashY,
            yoyo: true,
            duration: 160,
            onYoyo: () => {
                this.spawnMoveVFX(moveName, actorSpr.x, actorSpr.y, targetCoord.x, targetCoord.y, isAoE);
            },
            onComplete: () => {
                this.time.delayedCall(480, () => { if (callback) callback(); });
            }
        });
    }

    spawnMoveVFX(moveName, fromX, fromY, toX, toY, isAoE) {
        const moveLower = moveName.toLowerCase();

        // FOGO
        if (moveLower.includes('brasas') || moveLower.includes('chamas') || moveLower.includes('fogo')) {
            SoundEngine.attackFire();
            for (let i = 0; i < 10; i++) {
                const flame = this.add.circle(fromX, fromY, 8, 0xff5722, 0.95);
                this.tweens.add({
                    targets: flame,
                    x: toX + Phaser.Math.Between(-24, 24),
                    y: toY + Phaser.Math.Between(-24, 24),
                    scale: { from: 1, to: 3.5 },
                    alpha: { from: 1, to: 0 },
                    duration: 380 + i * 35,
                    onComplete: () => flame.destroy()
                });
            }
        }
        // ÁGUA
        else if (moveLower.includes('água') || moveLower.includes('surfar')) {
            SoundEngine.attackWater();
            if (isAoE) {
                const wave = this.add.rectangle(400, fromY, 740, 28, 0x00f0ff, 0.75);
                this.tweens.add({
                    targets: wave,
                    y: toY,
                    scaleY: 3.5,
                    alpha: 0,
                    duration: 420,
                    onComplete: () => wave.destroy()
                });
            } else {
                const blast = this.add.circle(fromX, fromY, 14, 0x29b6f6, 0.95);
                this.tweens.add({
                    targets: blast,
                    x: toX,
                    y: toY,
                    scale: 2.4,
                    duration: 320,
                    onComplete: () => blast.destroy()
                });
            }
        }
        // RAIO
        else if (moveLower.includes('trovão') || moveLower.includes('raio')) {
            SoundEngine.attackThunder();
            const bolt = this.add.graphics();
            bolt.lineStyle(5, 0xffeb3b, 1);
            bolt.strokePoints([
                { x: toX - 16, y: 0 }, { x: toX + 22, y: toY - 50 },
                { x: toX - 22, y: toY - 25 }, { x: toX, y: toY }
            ]);
            this.cameras.main.flash(140, 255, 235, 59, 0.35);
            this.time.delayedCall(260, () => bolt.destroy());
        }
        // TERREMOTO / ROCHA
        else if (moveLower.includes('terremoto') || moveLower.includes('rocha') || moveLower.includes('pedra')) {
            SoundEngine.attackRock();
            this.cameras.main.shake(360, 0.025);
            for (let i = 0; i < 7; i++) {
                const rock = this.add.rectangle(toX + Phaser.Math.Between(-45, 45), toY - 75, 12, 12, 0x8d6e63);
                this.tweens.add({
                    targets: rock,
                    y: toY + Phaser.Math.Between(-14, 14),
                    angle: 180,
                    duration: 260 + i * 30,
                    onComplete: () => rock.destroy()
                });
            }
        }
        // FÍSICO / CORTE
        else {
            SoundEngine.attackPhysical();
            const spark = this.add.star(toX, toY, 5, 5, 16, 0xffffff);
            this.tweens.add({
                targets: spark,
                scale: 3,
                alpha: 0,
                duration: 260,
                onComplete: () => spark.destroy()
            });
        }
    }

    playFaint(side, idx) {
        const spr = this.monSprites[side][idx];
        const sh = this.shadows[side][idx];
        const ped = this.pedestals[side][idx];
        if (sh) sh.setAlpha(0);
        if (ped) ped.setAlpha(0.1);
        if (!spr) return;
        this.tweens.add({
            targets: spr,
            y: spr.y + 18,
            alpha: 0.2,
            tint: 0x444444,
            duration: 400
        });
    }
}

function initPhaserStadium() {
    if (phaserGame) return;
    const config = {
        type: Phaser.AUTO,
        parent: 'phaser-stadium-canvas',
        width: 800,
        height: 360,
        transparent: false,
        scene: [StadiumScene],
        scale: {
            mode: Phaser.Scale.FIT,
            autoCenter: Phaser.Scale.CENTER_BOTH
        }
    };
    phaserGame = new Phaser.Game(config);
}

// ================= INICIALIZAÇÃO DO COMBATE STADIUM =================
async function startStadiumMatch() {
    SoundEngine.click();
    if (currentMatchIndex >= 3) {
        alert("🏆 Você já foi o grande Campeão deste torneio!");
        return;
    }

    const opp = tournamentOpponents[currentMatchIndex];

    const combatPlayerTeam = gameState.team.map(m => {
        const p = m.data;
        const statVal = name => p.stats.find(s => s.name.toLowerCase() === name)?.val || 45;
        const maxHp = Math.round((2 * statVal('hp') * m.level) / 100 + m.level + 10 + (m.bonusStats.hp || 0) * 2);
        return {
            id: p.id,
            name: p.name,
            sprite: p.sprite,
            sprite_animated: p.sprite_animated || `https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/showdown/${p.id}.gif`,
            types: p.types,
            level: m.level,
            stats: p.stats,
            bonus_stats: m.bonusStats,
            max_hp: maxHp,
            current_hp: maxHp,
            status: null,
            sleep_turns: 0,
            stat_buffs: { attack: 1.0, defense: 1.0, speed: 1.0 },
            moves: p.moves || []
        };
    });

    const combatOppTeam = opp.team.map(o => ({
        ...o,
        sprite_animated: o.sprite_animated || `https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/showdown/${o.id}.gif`,
        current_hp: o.max_hp,
        status: null,
        sleep_turns: 0,
        stat_buffs: { attack: 1.0, defense: 1.0, speed: 1.0 }
    }));

    stadiumBattle = {
        inBattle: true,
        playerTeam: combatPlayerTeam,
        oppTeam: combatOppTeam,
        oppTrainerName: opp.trainer_name,
        orders: [
            { pokemon_idx: 0, move_idx: 0, target_idx: 0 },
            { pokemon_idx: 1, move_idx: 0, target_idx: 1 },
            { pokemon_idx: 2, move_idx: 0, target_idx: 2 },
        ]
    };

    document.getElementById('tournament-overview').style.display = 'none';
    document.getElementById('stadium-arena-wrapper').classList.add('active');
    document.getElementById('battle-end-banner').classList.remove('active');
    document.getElementById('stadium-opp-trainer-tag').innerText = `Treinador: ${opp.trainer_name}`;

    document.getElementById('interactive-log').innerHTML = `
        <div style="color:var(--cyan);">🏟️ Batalha Stadium 3v3 iniciada contra <strong>${opp.trainer_name}</strong>!</div>
        <div>Escolha os golpes reais e alvos táticos para seus 3 Pokémon:</div>
    `;

    initPhaserStadium();

    if (stadiumScene) {
        loadFighterTexturesAndStart();
    } else {
        setTimeout(loadFighterTexturesAndStart, 300);
    }
}

function loadFighterTexturesAndStart() {
    if (!stadiumScene) return;

    const loads = [];
    const queueLoad = (key, src) => new Promise(resolve => {
        if (!src) { resolve(); return; }
        const img = new Image();
        img.crossOrigin = 'anonymous';
        img.onload = () => {
            try {
                if (stadiumScene && stadiumScene.textures) {
                    if (stadiumScene.textures.exists(key)) {
                        stadiumScene.textures.remove(key);
                    }
                    stadiumScene.textures.addImage(key, img);
                }
            } catch (e) {
                console.warn("Erro ao registrar textura:", e);
            }
            resolve();
        };
        img.onerror = () => resolve();
        img.src = src;
    });

    stadiumBattle.playerTeam.forEach((m, idx) => loads.push(queueLoad(`p_${idx}`, m.sprite)));
    stadiumBattle.oppTeam.forEach((m, idx) => loads.push(queueLoad(`opp_${idx}`, m.sprite)));

    Promise.all(loads).then(() => {
        if (stadiumScene) {
            stadiumScene.initFighters();
        }
        renderStadiumOrdersControls();
    });
}

// ================= RENDERIZADOR DOS FIGHTER COMMAND CARDS (3 COLUNAS & NOMES DOS ADVERSÁRIOS) =================
function renderStadiumOrdersControls() {
    const list = document.getElementById('stadium-orders-list');
    list.className = 'fighters-cmd-grid-3cols';

    list.innerHTML = stadiumBattle.playerTeam.map((m, idx) => {
        const isFainted = m.current_hp <= 0;
        const order = stadiumBattle.orders[idx];
        const isCaptain = idx === 1;
        const hpPct = Math.max(0, (m.current_hp / m.max_hp) * 100);
        const hpColor = hpPct <= 20 ? 'var(--primary-color)' : hpPct <= 50 ? 'var(--gold)' : 'var(--green)';

        if (isFainted) {
            return `
                <div class="fighter-cmd-card fainted">
                    <div class="fighter-card-meta">
                        <div class="fighter-avatar-box">
                            <img src="${m.sprite}" alt="${m.name}">
                        </div>
                        <div class="fighter-card-title">
                            <div class="fighter-title-row">
                                <strong>${m.name} [${POS_LABELS[idx]}]</strong>
                                <small style="color:var(--primary-color); font-weight:800;">💀 Nocauteado</small>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }

        // 4 Botões de Golpes Reais Arcade
        const movesHTML = m.moves.map((mv, mIdx) => {
            const isSelected = order.move_idx === mIdx;
            const tColor = TYPE_COLORS[mv.type.toLowerCase()] || '#777';
            const catIcon = mv.category === 'special' ? '🔮' : mv.category === 'status' ? '⚡' : mv.category === 'buff' ? '🛡️' : mv.category === 'heal' ? '💚' : '⚔️';
            const catLabel = mv.category === 'special' ? 'Especial' : mv.category === 'status' ? 'Status' : mv.category === 'buff' ? 'Buff' : mv.category === 'heal' ? 'Cura' : 'Físico';

            return `
                <button class="move-btn ${isSelected ? 'selected' : ''}" onclick="selectMoveOrder(${idx}, ${mIdx})">
                    <div class="move-btn-name">${catIcon} ${mv.name}</div>
                    <div class="move-btn-sub">
                        <span class="move-type-pill" style="background:${tColor};">${mv.type.toUpperCase()}</span>
                        <span>${mv.power > 0 ? `Pwr ${mv.power}` : catLabel}</span>
                    </div>
                </button>
            `;
        }).join('');

        // Seletor de Alvos Tático COM NOME REAL DOS OPONENTES
        const currentMove = m.moves[order.move_idx] || m.moves[0];
        let targetSelectorHTML = '';

        if (currentMove.target_type === 'all_opponents') {
            targetSelectorHTML = `<div class="target-badge-aoe">🌊 TODOS OS OPONENTES (GOLPE DE ÁREA)</div>`;
        } else if (currentMove.target_type === 'self') {
            targetSelectorHTML = `<div class="target-badge-self">💪 AUTO-ALVO (BUFF/CURA NO PRÓPRIO POKÉMON)</div>`;
        } else {
            const validReach = idx === 0 ? [0, 1] : idx === 1 ? [0, 1, 2] : [1, 2];
            const aliveOpponents = [0, 1, 2].filter(t => stadiumBattle.oppTeam[t]?.current_hp > 0);
            const reachAndAlive = validReach.filter(t => stadiumBattle.oppTeam[t]?.current_hp > 0);
            const selectableTargets = reachAndAlive.length > 0 ? reachAndAlive : aliveOpponents;

            targetSelectorHTML = `
                <span class="target-label">Alvo:</span>
                ${[0, 1, 2].map(tIdx => {
                    const oppMon = stadiumBattle.oppTeam[tIdx];
                    const isAlive = oppMon && oppMon.current_hp > 0;
                    const canTarget = selectableTargets.includes(tIdx);
                    const isTargetSelected = order.target_idx === tIdx;
                    const posEmoji = tIdx === 0 ? '👈' : tIdx === 1 ? '🎯' : '👉';
                    const oppName = oppMon ? oppMon.name : (tIdx === 0 ? 'Esquerda' : tIdx === 1 ? 'Centro' : 'Direita');
                    const targetBtnText = canTarget ? `${posEmoji} ${oppName}` : `🚫 ${oppName}`;
                    const targetTitle = !canTarget ? `${oppName} está fora de alcance desta posição` : `Mirar em ${oppName}`;

                    return `
                        <button class="target-btn ${isTargetSelected ? 'selected' : ''} ${!canTarget ? 'disabled' : ''}" 
                                onclick="selectTargetOrder(${idx}, ${tIdx})"
                                title="${targetTitle}">
                            ${targetBtnText}
                        </button>
                    `;
                }).join('')}
            `;
        }

        return `
            <div class="fighter-cmd-card ${isCaptain ? 'captain' : ''}">
                <div class="fighter-card-meta">
                    <div class="fighter-avatar-box">
                        <img src="${m.sprite_animated || m.sprite}" alt="${m.name}">
                    </div>
                    <div class="fighter-card-title">
                        <div class="fighter-title-row">
                            <strong>${m.name} <span style="font-size:0.72rem; color:var(--cyan);">Nv. ${m.level}</span></strong>
                            <span class="badge" style="background:${isCaptain ? 'var(--gold)' : 'var(--cyan)'}; color:#111; font-size:0.62rem; font-weight:800; padding:2px 7px; border-radius:4px;">
                                ${POS_LABELS[idx]} ${isCaptain ? '👑' : ''}
                            </span>
                        </div>
                        <div class="fighter-hp-mini-wrap">
                            <div class="fighter-hp-mini-bar">
                                <div class="fighter-hp-mini-fill" style="width:${hpPct}%; background:${hpColor};"></div>
                            </div>
                            <span class="fighter-hp-text">${m.current_hp}/${m.max_hp} HP</span>
                        </div>
                    </div>
                </div>
                <div class="moves-grid">
                    ${movesHTML}
                </div>
                <div class="target-selector-row">
                    ${targetSelectorHTML}
                </div>
            </div>
        `;
    }).join('');
}

function selectMoveOrder(pokemonIdx, moveIdx) {
    SoundEngine.selectMove();
    stadiumBattle.orders[pokemonIdx].move_idx = moveIdx;
    renderStadiumOrdersControls();
}

function selectTargetOrder(pokemonIdx, targetIdx) {
    SoundEngine.click();
    stadiumBattle.orders[pokemonIdx].target_idx = targetIdx;
    renderStadiumOrdersControls();
}

async function executeStadiumTurn() {
    SoundEngine.click();
    document.getElementById('btn-exec-stadium-turn').disabled = true;
    const aliveOrders = stadiumBattle.orders.filter(o => stadiumBattle.playerTeam[o.pokemon_idx]?.current_hp > 0);

    try {
        const res = await fetch('/api/battle/triple_turn', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                player_team: stadiumBattle.playerTeam,
                opponent_team: stadiumBattle.oppTeam,
                player_orders: aliveOrders,
                opponent_trainer_name: stadiumBattle.oppTrainerName
            })
        });

        const data = await res.json();
        stadiumBattle.playerTeam = data.player_team;
        stadiumBattle.oppTeam = data.opponent_team;

        const logDiv = document.getElementById('interactive-log');
        const toPhaserSide = s => s === 'opponent' ? 'opp' : s;

        const runStep = (stepIdx) => {
            if (stepIdx >= data.steps.length) {
                if (stadiumScene) {
                    stadiumBattle.playerTeam.forEach((m, i) => {
                        stadiumScene.updateHPBar('player', i, m.current_hp, m.max_hp);
                        if (m.current_hp <= 0) stadiumScene.playFaint('player', i);
                    });
                    stadiumBattle.oppTeam.forEach((m, i) => {
                        stadiumScene.updateHPBar('opp', i, m.current_hp, m.max_hp);
                        if (m.current_hp <= 0) stadiumScene.playFaint('opp', i);
                    });
                }

                renderStadiumOrdersControls();

                // Fim de Batalha
                if (data.is_finished) {
                    const banner = document.getElementById('battle-end-banner');
                    const title = document.getElementById('battle-end-title');
                    const reward = document.getElementById('battle-end-reward');
                    banner.classList.add('active');

                    if (data.winner === 'player') {
                        SoundEngine.victory();
                        title.innerText = '🏆 VITÓRIA NO ESTÁDIO 3v3!';
                        title.style.color = 'var(--green)';
                        reward.innerText = `Recompensas: +${data.xp_earned} XP para cada um dos seus 3 Pokémon • +${data.coins_earned} PokéMoedas!`;

                        gameState.coins += data.coins_earned;
                        gameState.team.forEach(m => {
                            m.xp += data.xp_earned;
                            const needed = m.level * 100;
                            if (m.xp >= needed && m.level < 50) {
                                m.xp -= needed;
                                m.level += 1;
                            }
                        });
                        currentMatchIndex++;
                    } else {
                        SoundEngine.defeat();
                        title.innerText = '💀 DERROTA!';
                        title.style.color = 'var(--primary-color)';
                        reward.innerText = `Seu time foi derrotado. Treine no Dojo e tente novamente (+${data.xp_earned} XP).`;
                        gameState.coins += data.coins_earned;
                        gameState.team.forEach(m => { m.xp += data.xp_earned; });
                    }

                    saveGame();
                    renderTeamSlots();
                } else {
                    document.getElementById('btn-exec-stadium-turn').disabled = false;
                }
                return;
            }

            const step = data.steps[stepIdx];
            step.logs.forEach(line => {
                const l = document.createElement('div');
                l.innerHTML = line;
                logDiv.appendChild(l);
            });
            logDiv.scrollTop = logDiv.scrollHeight;

            const next = () => runStep(stepIdx + 1);

            if (stadiumScene && (step.kind === 'damage' || step.kind === 'status' || step.kind === 'buff' || step.kind === 'heal')) {
                stadiumScene.playAttackVFX(
                    toPhaserSide(step.side),
                    step.actor_idx,
                    toPhaserSide(step.target_side),
                    step.target_idx,
                    step.move_name || '',
                    step.is_aoe,
                    () => {
                        stadiumBattle.playerTeam.forEach((m, i) => stadiumScene.updateHPBar('player', i, m.current_hp, m.max_hp));
                        stadiumBattle.oppTeam.forEach((m, i) => stadiumScene.updateHPBar('opp', i, m.current_hp, m.max_hp));
                        next();
                    }
                );
            } else {
                if (stadiumScene && step.kind === 'tick') {
                    stadiumBattle.playerTeam.forEach((m, i) => stadiumScene.updateHPBar('player', i, m.current_hp, m.max_hp));
                    stadiumBattle.oppTeam.forEach((m, i) => stadiumScene.updateHPBar('opp', i, m.current_hp, m.max_hp));
                }
                setTimeout(next, 350);
            }
        };

        runStep(0);

    } catch (err) {
        console.error("Erro no turno Stadium:", err);
        document.getElementById('btn-exec-stadium-turn').disabled = false;
    }
}

function closeStadiumBattle() {
    SoundEngine.click();
    document.getElementById('stadium-arena-wrapper').classList.remove('active');
    document.getElementById('tournament-overview').style.display = 'block';
    renderBracket();
    updateUI();
}

async function init() {
    await fetchRankDPool();
    loadGame();
}

init();

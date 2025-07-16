import discord
from discord.ext import commands
import json
import asyncio
import random
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration du bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# Base de données simple (JSON)
class Database:
    def __init__(self):
        self.players_file = 'players.json'
        self.clans_file = 'clans.json'
    
    def load_players(self):
        try:
            with open(self.players_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def save_players(self, data):
        with open(self.players_file, 'w') as f:
            json.dump(data, f, indent=2)

db = Database()

# Classes de base
class Player:
    def __init__(self, user_id, username):
        self.user_id = user_id
        self.username = username
        self.level = 1
        self.experience = 0
        self.chakra = 100
        self.health = 100
        self.max_health = 100
        self.max_chakra = 100
        self.village = None
        self.clan = None
        self.stats = {
            "ninjutsu": 10,
            "taijutsu": 10,
            "genjutsu": 10,
            "intelligence": 10,
            "force": 10,
            "vitesse": 10
        }
        self.ryo = 1000
        self.rank = "Étudiant de l'Académie"
        self.last_mission = None
        self.inventory = []
        self.jutsu = []
        self.clan_rerolls = 3  # Nombre de rerolls gratuits

class Clan:
    def __init__(self, name, description, stat_bonus, special_jutsu, rarity="commun"):
        self.name = name
        self.description = description
        self.stat_bonus = stat_bonus  # Dict des bonus de stats
        self.special_jutsu = special_jutsu
        self.rarity = rarity

# Clans disponibles
CLANS = [
    # Clans légendaires (rares)
    Clan("Uchiha", "Clan du Sharingan", {"ninjutsu": 15, "intelligence": 10}, ["Katon: Goukakyuu no Jutsu", "Sharingan"], "légendaire"),
    Clan("Hyuga", "Clan du Byakugan", {"taijutsu": 15, "vitesse": 10}, ["Juken", "Byakugan"], "légendaire"),
    Clan("Senju", "Clan de la Volonté du Feu", {"force": 15, "ninjutsu": 10}, ["Mokuton: Jukai Kotan"], "légendaire"),
    
    # Clans rares
    Clan("Nara", "Clan des ombres", {"intelligence": 20, "genjutsu": 5}, ["Kagemane no Jutsu"], "rare"),
    Clan("Akimichi", "Clan de l'expansion", {"force": 20, "taijutsu": 5}, ["Baika no Jutsu"], "rare"),
    Clan("Yamanaka", "Clan de l'esprit", {"intelligence": 15, "genjutsu": 10}, ["Shintenshin no Jutsu"], "rare"),
    Clan("Inuzuka", "Clan des chiens", {"vitesse": 15, "taijutsu": 10}, ["Gatsuga"], "rare"),
    Clan("Aburame", "Clan des insectes", {"intelligence": 15, "ninjutsu": 10}, ["Kikaichū no Jutsu"], "rare"),
    
    # Clans communs
    Clan("Sarutobi", "Clan du Hokage", {"ninjutsu": 10, "intelligence": 5}, ["Katon: Endan"], "commun"),
    Clan("Hatake", "Clan du chien argenté", {"vitesse": 10, "taijutsu": 5}, ["Chidori"], "commun"),
    Clan("Shimura", "Clan de la racine", {"intelligence": 8, "ninjutsu": 7}, ["Futon: Shinkuugyoku"], "commun"),
    Clan("Mitarashi", "Clan du serpent", {"vitesse": 8, "genjutsu": 7}, ["Sen'eijashu"], "commun"),
    Clan("Morino", "Clan de l'interrogation", {"intelligence": 10, "genjutsu": 5}, ["Kanashibari no Jutsu"], "commun"),
    
    # Clan sans bloodline
    Clan("Sans Clan", "Ninja civil", {}, [], "commun"),
]

def get_random_clan():
    """Obtenir un clan aléatoire selon les probabilités de rareté"""
    weights = []
    for clan in CLANS:
        if clan.rarity == "légendaire":
            weights.append(5)  # 5% de chance
        elif clan.rarity == "rare":
            weights.append(15)  # 15% de chance
        else:
            weights.append(80)  # 80% de chance pour commun
    
    return random.choices(CLANS, weights=weights)[0]

def apply_clan_bonus(player_data, clan):
    """Appliquer les bonus de clan aux stats du joueur"""
    if clan and clan.stat_bonus:
        for stat, bonus in clan.stat_bonus.items():
            player_data['stats'][stat] += bonus
    
    if clan and clan.special_jutsu:
        for jutsu in clan.special_jutsu:
            if jutsu not in player_data['jutsu']:
                player_data['jutsu'].append(jutsu)

# Événements
@bot.event
async def on_ready():
    print(f'{bot.user} est connecté!')

@bot.command(name='creer')
async def create_character(ctx, village=None):
    """Créer un nouveau personnage"""
    players = db.load_players()
    user_id = str(ctx.author.id)
    
    if user_id in players:
        await ctx.send("❌ Vous avez déjà un personnage!")
        return
    
    villages = ["Konoha", "Suna", "Kiri", "Kumo", "Iwa"]
    if village not in villages:
        embed = discord.Embed(
            title="🏘️ Choisissez votre village",
            description=f"Villages disponibles: {', '.join(villages)}",
            color=0x00ff00
        )
        await ctx.send(embed=embed)
        return
    
    player = Player(user_id, ctx.author.display_name)
    player.village = village
    
    # Assigner un clan aléatoire
    clan = get_random_clan()
    player.clan = clan.__dict__
    
    # Convertir en dict et appliquer les bonus
    player_dict = player.__dict__
    apply_clan_bonus(player_dict, clan)
    
    players[user_id] = player_dict
    db.save_players(players)
    
    embed = discord.Embed(
        title="✅ Personnage créé!",
        description=f"Bienvenue à {village}, {ctx.author.display_name}!",
        color=0x00ff00
    )
    embed.add_field(name="Niveau", value=player.level, inline=True)
    embed.add_field(name="Village", value=village, inline=True)
    embed.add_field(name="Ryō", value=player.ryo, inline=True)
    embed.add_field(name="🏮 Clan", value=f"**{clan.name}** ({clan.rarity})", inline=False)
    embed.add_field(name="Description", value=clan.description, inline=False)
    
    if clan.special_jutsu:
        embed.add_field(name="🌟 Jutsu de clan", value=", ".join(clan.special_jutsu), inline=False)
    
    await ctx.send(embed=embed)

@bot.command(name='reroll_clan')
async def reroll_clan(ctx):
    """Reroll son clan"""
    players = db.load_players()
    user_id = str(ctx.author.id)
    
    if user_id not in players:
        await ctx.send("❌ Vous n'avez pas de personnage!")
        return
    
    player = players[user_id]
    
    # Vérifier si le joueur a des rerolls
    if player.get('clan_rerolls', 0) <= 0:
        cost = 500
        if player['ryo'] < cost:
            await ctx.send(f"❌ Plus de rerolls gratuits! Coût: {cost} Ryō (vous avez {player['ryo']} Ryō)")
            return
        player['ryo'] -= cost
        embed_title = f"🎲 Clan rerollé pour {cost} Ryō!"
    else:
        player['clan_rerolls'] -= 1
        embed_title = f"🎲 Clan rerollé! ({player['clan_rerolls']} rerolls gratuits restants)"
    
    # Sauvegarder l'ancien clan
    old_clan_name = player['clan']['name'] if player['clan'] else "Aucun"
    
    # Retirer les anciens bonus de clan
    if player['clan'] and player['clan']['stat_bonus']:
        for stat, bonus in player['clan']['stat_bonus'].items():
            player['stats'][stat] -= bonus
    
    # Retirer les anciens jutsu de clan
    if player['clan'] and player['clan']['special_jutsu']:
        for jutsu in player['clan']['special_jutsu']:
            if jutsu in player['jutsu']:
                player['jutsu'].remove(jutsu)
    
    # Nouveau clan
    new_clan = get_random_clan()
    player['clan'] = new_clan.__dict__
    
    # Appliquer les nouveaux bonus
    apply_clan_bonus(player, new_clan)
    
    db.save_players(players)
    
    embed = discord.Embed(
        title=embed_title,
        color=0x9932CC
    )
    embed.add_field(name="Ancien clan", value=old_clan_name, inline=True)
    embed.add_field(name="Nouveau clan", value=f"**{new_clan.name}** ({new_clan.rarity})", inline=True)
    embed.add_field(name="Description", value=new_clan.description, inline=False)
    
    if new_clan.special_jutsu:
        embed.add_field(name="🌟 Nouveaux jutsu", value=", ".join(new_clan.special_jutsu), inline=False)
    
    if new_clan.stat_bonus:
        bonus_text = ", ".join([f"{stat.capitalize()}: +{bonus}" for stat, bonus in new_clan.stat_bonus.items()])
        embed.add_field(name="📈 Bonus de stats", value=bonus_text, inline=False)
    
    await ctx.send(embed=embed)

@bot.command(name='clans')
async def clans_list(ctx):
    """Afficher la liste des clans disponibles"""
    embed = discord.Embed(
        title="🏮 Clans disponibles",
        description="Voici tous les clans que vous pouvez obtenir:",
        color=0x9932CC
    )
    
    # Grouper par rareté
    legendaires = [c for c in CLANS if c.rarity == "légendaire"]
    rares = [c for c in CLANS if c.rarity == "rare"]
    communs = [c for c in CLANS if c.rarity == "commun"]
    
    if legendaires:
        leg_text = "\n".join([f"**{c.name}** - {c.description}" for c in legendaires])
        embed.add_field(name="🌟 Légendaires (5%)", value=leg_text, inline=False)
    
    if rares:
        rare_text = "\n".join([f"**{c.name}** - {c.description}" for c in rares])
        embed.add_field(name="💎 Rares (15%)", value=rare_text, inline=False)
    
    if communs:
        common_text = "\n".join([f"**{c.name}** - {c.description}" for c in communs])
        embed.add_field(name="⚪ Communs (80%)", value=common_text, inline=False)
    
    embed.add_field(name="💰 Reroll", value="3 rerolls gratuits, puis 500 Ryō par reroll", inline=False)
    
    await ctx.send(embed=embed)

@bot.command(name='missions')
async def missions(ctx):
    """Afficher les missions disponibles"""
    embed = discord.Embed(
        title="📝 Missions disponibles",
        color=0xffcc00
    )
    
    for mission in MISSIONS:
        embed.add_field(
            name=f"{mission.name} ({mission.rank})",
            value=f"**Description:** {mission.description}\n**Récompense:** {mission.reward_exp} XP, {mission.reward_ryo} Ryō\n**Niveau requis:** {mission.required_level}",
            inline=False
        )
    
    await ctx.send(embed=embed)

@bot.command(name='mission')
async def join_mission(ctx, *, mission_name: str):
    """Rejoindre une mission"""
    players = db.load_players()
    user_id = str(ctx.author.id)
    
    if user_id not in players:
        await ctx.send("❌ Vous n'avez pas de personnage! Créez-en un avec `!creer <village>`.")
        return
    
    player = players[user_id]
    
    if player['last_mission'] is not None:
        await ctx.send("❌ Vous avez déjà une mission en cours! Terminez-la avec `!terminer_mission` ou quittez-la avec `!quitter_mission`.")
        return
    
    mission = next((m for m in MISSIONS if m.name.lower() == mission_name.lower()), None)
    if mission is None:
        await ctx.send("❌ Mission non trouvée! Utilisez `!missions` pour voir la liste.")
        return
    
    if player['level'] < mission.required_level:
        await ctx.send(f"❌ Vous devez être au moins niveau {mission.required_level} pour cette mission.")
        return
    
    player['last_mission'] = mission.__dict__
    db.save_players(players)
    
    embed = discord.Embed(
        title="✅ Mission acceptée!",
        description=f"**{mission.name}**\n{mission.description}",
        color=0x00ff00
    )
    embed.add_field(name="Récompense", value=f"{mission.reward_exp} XP, {mission.reward_ryo} Ryō", inline=False)
    await ctx.send(embed=embed)

@bot.command(name='terminer_mission')
async def complete_mission(ctx):
    """Terminer la mission en cours"""
    players = db.load_players()
    user_id = str(ctx.author.id)
    
    if user_id not in players:
        await ctx.send("❌ Vous n'avez pas de personnage!")
        return
    
    player = players[user_id]
    
    if player['last_mission'] is None:
        await ctx.send("❌ Vous n'avez pas de mission en cours.")
        return
    
    mission = player['last_mission']
    
    # Simulation de réussite (70% de chance)
    success = random.random() > 0.3
    
    if success:
        player['experience'] += mission['reward_exp']
        player['ryo'] += mission['reward_ryo']
        
        # Vérifier montée de niveau
        level_up = False
        while player['experience'] >= (player['level'] * 100):
            player['experience'] -= (player['level'] * 100)
            player['level'] += 1
            player['max_health'] += 10
            player['max_chakra'] += 10
            player['health'] = player['max_health']
            player['chakra'] = player['max_chakra']
            level_up = True
        
        embed = discord.Embed(
            title="🎉 Mission réussie!",
            description=f"Vous avez terminé: **{mission['name']}**",
            color=0x00ff00
        )
        embed.add_field(name="Récompenses", value=f"+{mission['reward_exp']} XP\n+{mission['reward_ryo']} Ryō", inline=False)
        
        if level_up:
            embed.add_field(name="🆙 Niveau supérieur!", value=f"Vous êtes maintenant niveau {player['level']}!", inline=False)
    else:
        embed = discord.Embed(
            title="❌ Mission échouée!",
            description=f"Vous avez échoué: **{mission['name']}**",
            color=0xff0000
        )
        embed.add_field(name="Conséquences", value="Aucune récompense reçue.", inline=False)
    
    player['last_mission'] = None
    db.save_players(players)
    await ctx.send(embed=embed)

@bot.command(name='quitter_mission')
async def leave_mission(ctx):
    """Quitter la mission en cours"""
    players = db.load_players()
    user_id = str(ctx.author.id)
    
    if user_id not in players:
        await ctx.send("❌ Vous n'avez pas de personnage!")
        return
    
    player = players[user_id]
    
    if player['last_mission'] is None:
        await ctx.send("❌ Vous n'avez pas de mission en cours.")
        return
    
    mission_name = player['last_mission']['name']
    player['last_mission'] = None
    db.save_players(players)
    
    await ctx.send(f"✅ Vous avez quitté la mission: **{mission_name}**")

@bot.command(name='xp')
async def add_xp(ctx, amount: int):
    """Ajouter de l'XP à un joueur (admin seulement)"""
    # Remplacez par votre ID Discord
    if ctx.author.id != 1395142435981492324:  
        await ctx.send("❌ Vous n'avez pas la permission d'utiliser cette commande.")
        return
    
    players = db.load_players()
    user_id = str(ctx.author.id)
    
    if user_id not in players:
        await ctx.send("❌ Vous n'avez pas de personnage!")
        return
    
    player = players[user_id]
    player['experience'] += amount
    
    # Vérifier montée de niveau
    level_up = False
    while player['experience'] >= (player['level'] * 100):
        player['experience'] -= (player['level'] * 100)
        player['level'] += 1
        player['max_health'] += 10
        player['max_chakra'] += 10
        player['health'] = player['max_health']
        player['chakra'] = player['max_chakra']
        level_up = True
    
    db.save_players(players)
    
    if level_up:
        await ctx.send(f"✅ {amount} XP ajouté. 🎉 Vous êtes maintenant niveau {player['level']}!")
    else:
        await ctx.send(f"✅ {amount} XP ajouté.")

@bot.command(name='shop')
async def shop(ctx):
    """Afficher les objets disponibles à l'achat"""
    items = [
        {"name": "Potion de soin", "price": 50, "effect": "Restaure 50 PV"},
        {"name": "Potion de chakra", "price": 50, "effect": "Restaure 50 Chakra"},
        {"name": "Élixir de sagesse", "price": 100, "effect": "Donne 10 XP"},
        {"name": "Scroll de jutsu", "price": 150, "effect": "Apprend un jutsu aléatoire"},
    ]
    
    embed = discord.Embed(
        title="🛒 Boutique",
        color=0x00ff00
    )
    
    for item in items:
        embed.add_field(
            name=item["name"],
            value=f"**Prix:** {item['price']} Ryō\n**Effet:** {item['effect']}",
            inline=False
        )
    
    await ctx.send(embed=embed)

@bot.command(name='acheter')
async def buy(ctx, *, item_name: str):
    """Acheter un objet"""
    players = db.load_players()
    user_id = str(ctx.author.id)
    
    if user_id not in players:
        await ctx.send("❌ Vous n'avez pas de personnage!")
        return
    
    player = players[user_id]
    
    items = {
        "potion de soin": {"price": 50, "effect": "heal", "amount": 50},
        "potion de chakra": {"price": 50, "effect": "chakra", "amount": 50},
        "élixir de sagesse": {"price": 100, "effect": "xp", "amount": 10},
        "scroll de jutsu": {"price": 150, "effect": "jutsu", "amount": 1},
    }
    
    item = items.get(item_name.lower())
    if item is None:
        await ctx.send("❌ Objet non trouvé! Utilisez `!shop` pour voir les objets disponibles.")
        return
    
    if player['ryo'] < item["price"]:
        await ctx.send(f"❌ Vous n'avez pas assez de Ryō! Coût: {item['price']} Ryō")
        return
    
    player['ryo'] -= item["price"]
    
    if item["effect"] == "heal":
        player['health'] = min(player['max_health'], player['health'] + item["amount"])
        await ctx.send(f"✅ Vous avez acheté une **{item_name}**. Vos PV sont maintenant à {player['health']}/{player['max_health']}.")
    elif item["effect"] == "chakra":
        player['chakra'] = min(player['max_chakra'], player['chakra'] + item["amount"])
        await ctx.send(f"✅ Vous avez acheté une **{item_name}**. Votre Chakra est maintenant à {player['chakra']}/{player['max_chakra']}.")
    elif item["effect"] == "xp":
        player['experience'] += item["amount"]
        await ctx.send(f"✅ Vous avez acheté un **{item_name}**. Vous avez gagné {item['amount']} XP.")
    elif item["effect"] == "jutsu":
        jutsu_list = ["Katon: Goukakyuu", "Suiton: Mizurappa", "Doton: Doryuuheki", "Fuuton: Daitoppa", "Raiton: Chidori"]
        new_jutsu = random.choice(jutsu_list)
        if new_jutsu not in player['jutsu']:
            player['jutsu'].append(new_jutsu)
            await ctx.send(f"✅ Vous avez acheté un **{item_name}**. Vous avez appris: **{new_jutsu}**!")
        else:
            await ctx.send(f"✅ Vous avez acheté un **{item_name}**, mais vous connaissiez déjà le jutsu!")
    
    db.save_players(players)

@bot.command(name='heal')
async def heal(ctx):
    """Se soigner"""
    players = db.load_players()
    user_id = str(ctx.author.id)
    
    if user_id not in players:
        await ctx.send("❌ Vous n'avez pas de personnage!")
        return
    
    player = players[user_id]
    
    heal_cost = 10
    
    if player['chakra'] < heal_cost:
        await ctx.send("❌ Vous n'avez pas assez de Chakra pour vous soigner.")
        return
    
    if player['health'] >= player['max_health']:
        await ctx.send("❌ Vous êtes déjà en pleine santé!")
        return
    
    player['chakra'] -= heal_cost
    player['health'] = min(player['max_health'], player['health'] + 20)
    db.save_players(players)
    
    await ctx.send(f"✅ Vous vous êtes soigné. Vos PV sont maintenant à {player['health']}/{player['max_health']}.")

@bot.command(name='jutsu')
async def jutsu_list(ctx):
    """Afficher vos jutsu"""
    players = db.load_players()
    user_id = str(ctx.author.id)
    
    if user_id not in players:
        await ctx.send("❌ Vous n'avez pas de personnage!")
        return
    
    player = players[user_id]
    
    if not player['jutsu']:
        await ctx.send("❌ Vous ne connaissez aucun jutsu! Achetez un scroll de jutsu dans la boutique.")
        return
    
    embed = discord.Embed(
        title=f"📜 Jutsu de {ctx.author.display_name}",
        color=0x9932CC
    )
    
    jutsu_text = "\n".join([f"• {jutsu}" for jutsu in player['jutsu']])
    embed.add_field(name="Techniques connues", value=jutsu_text, inline=False)
    
    await ctx.send(embed=embed)

@bot.command(name='help')
async def help_command(ctx):
    """Afficher l'aide"""
    embed = discord.Embed(
        title="🆘 Aide des commandes",
        description="Voici toutes les commandes disponibles:",
        color=0x00ff00
    )
    
    # Commandes de base
    embed.add_field(name="**Commandes de base**", value="", inline=False)
    embed.add_field(name="`!creer <village>`", value="Créer un nouveau personnage", inline=False)
    embed.add_field(name="`!profil [@membre]`", value="Afficher le profil d'un joueur", inline=False)
    embed.add_field(name="`!jutsu`", value="Afficher vos jutsu", inline=False)
    
    # Clans
    embed.add_field(name="**Système de clans**", value="", inline=False)
    embed.add_field(name="`!clans`", value="Afficher tous les clans disponibles", inline=False)
    embed.add_field(name="`!reroll_clan`", value="Reroll votre clan", inline=False)
    
    # Missions
    embed.add_field(name="**Missions**", value="", inline=False)
    embed.add_field(name="`!missions`", value="Afficher les missions disponibles", inline=False)
    embed.add_field(name="`!mission <nom>`", value="Rejoindre une mission", inline=False)
    embed.add_field(name="`!terminer_mission`", value="Terminer la mission en cours", inline=False)
    embed.add_field(name="`!quitter_mission`", value="Quitter la mission en cours", inline=False)
    
    # Boutique
    embed.add_field(name="**Boutique & Soins**", value="", inline=False)
    embed.add_field(name="`!shop`", value="Afficher la boutique", inline=False)
    embed.add_field(name="`!acheter <objet>`", value="Acheter un objet", inline=False)
    embed.add_field(name="`!heal`", value="Se soigner (coûte du chakra)", inline=False)
    
    await ctx.send(embed=embed)

# Démarrage du bot
if __name__ == "__main__":
    token = os.getenv('DISCORD_BOT_TOKEN')
    if not token:
        print("❌ Erreur: Token Discord non trouvé dans le fichier .env!")
    else:
        bot.run(token)
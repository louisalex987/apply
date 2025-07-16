import discord
from discord.ext import commands
import json
from datetime import datetime, timedelta

class PlayerCog(commands.Cog):
    def __init__(self, bot, db):
        self.bot = bot
        self.db = db
        
        self.villages = {
            "🍃": "Konoha",
            "💨": "Suna",
            "💧": "Kiri", 
            "⚡": "Kumo",
            "🗻": "Iwa"
        }
        
        self.clans = {
            "Konoha": ["Uchiha", "Hyuga", "Nara", "Akimichi", "Inuzuka"],
            "Suna": ["Sabaku", "Pakura", "Chikamatsu"],
            "Kiri": ["Hozuki", "Yuki", "Kaguya"],
            "Kumo": ["Yotsuki", "Darui"],
            "Iwa": ["Kamizuru", "Explosion Corps"]
        }

    @commands.command(name='start')
    async def start_game(self, ctx):
        """Commence l'aventure ninja"""
        player = await self.db.get_player(ctx.author.id)
        if player:
            await ctx.send("Vous avez déjà commencé votre aventure ninja!")
            return
        
        embed = discord.Embed(
            title="🥷 Bienvenue dans le monde de Naruto!",
            description="Choisissez votre village ninja:",
            color=0xFF6B35
        )
        
        for emoji, village in self.villages.items():
            embed.add_field(name=f"{emoji} {village}", value="​", inline=True)
        
        message = await ctx.send(embed=embed)
        
        for emoji in self.villages.keys():
            await message.add_reaction(emoji)
        
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in self.villages.keys()
        
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
            village = self.villages[str(reaction.emoji)]
            
            # Choix du clan
            clan_embed = discord.Embed(
                title=f"Village: {village}",
                description="Choisissez votre clan:",
                color=0xFF6B35
            )
            
            clan_options = self.clans.get(village, [])
            for i, clan in enumerate(clan_options, 1):
                clan_embed.add_field(name=f"{i}. {clan}", value="​", inline=False)
            
            await ctx.send(embed=clan_embed)
            
            def clan_check(msg):
                return msg.author == ctx.author and msg.content.isdigit()
            
            clan_msg = await self.bot.wait_for('message', timeout=60.0, check=clan_check)
            clan_choice = int(clan_msg.content) - 1
            
            if 0 <= clan_choice < len(clan_options):
                clan = clan_options[clan_choice]
                
                # Demande du nom
                await ctx.send("Choisissez votre nom de ninja:")
                
                def name_check(msg):
                    return msg.author == ctx.author and len(msg.content) <= 20
                
                name_msg = await self.bot.wait_for('message', timeout=60.0, check=name_check)
                name = name_msg.content
                
                # Création du joueur
                await self.db.create_player(ctx.author.id, name, village, clan)
                
                success_embed = discord.Embed(
                    title="🎉 Ninja créé avec succès!",
                    description=f"**Nom:** {name}\n**Village:** {village}\n**Clan:** {clan}",
                    color=0x00FF00
                )
                await ctx.send(embed=success_embed)
            
        except asyncio.TimeoutError:
            await ctx.send("Temps écoulé! Utilisez `!start` pour recommencer.")

    @commands.command(name='profil')
    async def profile(self, ctx, member: discord.Member = None):
        """Affiche le profil d'un ninja"""
        if member is None:
            member = ctx.author
        
        player = await self.db.get_player(member.id)
        if not player:
            await ctx.send("Ce ninja n'a pas encore commencé son aventure!")
            return
        
        stats = json.loads(player['stats'])
        
        embed = discord.Embed(
            title=f"🥷 Profil de {player['name']}",
            color=0x0099FF
        )
        
        embed.add_field(name="Village", value=player['village'], inline=True)
        embed.add_field(name="Clan", value=player['clan'] or "Aucun", inline=True)
        embed.add_field(name="Niveau", value=player['level'], inline=True)
        
        embed.add_field(name="💚 Santé", value=f"{player['health']}/100", inline=True)
        embed.add_field(name="💙 Chakra", value=f"{player['chakra']}/100", inline=True)
        embed.add_field(name="💛 Stamina", value=f"{player['stamina']}/100", inline=True)
        
        embed.add_field(name="💰 Ryo", value=player['ryo'], inline=True)
        embed.add_field(name="⭐ EXP", value=f"{player['exp']}/{player['level'] * 100}", inline=True)
        embed.add_field(name="​", value="​", inline=True)
        
        stats_text = "\n".join([f"**{stat.title()}:** {value}" for stat, value in stats.items()])
        embed.add_field(name="📊 Statistiques", value=stats_text, inline=False)
        
        await ctx.send(embed=embed)

    @commands.command(name='daily')
    async def daily_reward(self, ctx):
        """Récupère la récompense quotidienne"""
        player = await self.db.get_player(ctx.author.id)
        if not player:
            await ctx.send("Vous devez d'abord commencer votre aventure avec `!start`")
            return
        
        now = datetime.now()
        last_daily = datetime.fromisoformat(player['last_daily']) if player['last_daily'] else None
        
        if last_daily and now - last_daily < timedelta(days=1):
            next_daily = last_daily + timedelta(days=1)
            await ctx.send(f"Vous avez déjà récupéré votre récompense! Prochaine: {next_daily.strftime('%H:%M:%S')}")
            return
        
        reward_ryo = 100 + (player['level'] * 10)
        reward_exp = 50 + (player['level'] * 5)
        
        new_ryo = player['ryo'] + reward_ryo
        new_exp = player['exp'] + reward_exp
        
        await self.db.update_player(
            ctx.author.id,
            ryo=new_ryo,
            exp=new_exp,
            last_daily=now.isoformat()
        )
        
        embed = discord.Embed(
            title="🎁 Récompense quotidienne!",
            description=f"**+{reward_ryo} Ryo**\n**+{reward_exp} EXP**",
            color=0xFFD700
        )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(PlayerCog(bot))
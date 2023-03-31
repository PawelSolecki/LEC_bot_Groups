from datetime import date
import discord,sys,os
from discord.ext import commands
from discord import app_commands

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

import controllers.db as db
import resources.bot_functions as bot_functions
import resources.const as const
import models.models as models

class Test(commands.Cog):
    def __init__(self,bot):
        self.bot = bot

    # #set_channel - koemnda do wybrania kanalu na ktory ma wyslac glosowanie (stare config)
    # @commands.hybrid_command(name="set_channel",with_app_command=True, description = "Use it to set voting channel")
    # async def setChannel(self,ctx, channel:discord.channel.TextChannel):
    #     db.insertQuery(models.Server(ctx.message.guild.id,ctx.message.guild.name,channel.id).toDbServers()) 
    #     await ctx.send(embed = bot_functions.f_embed("Success ✅", "Channel has been set successfully", const.color_admin),ephemeral=True)


async def setup(bot):
    await bot.add_cog(Test(bot))
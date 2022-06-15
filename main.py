import os
import discord
from discord.ext import commands

import firebase_admin
from firebase_admin import credentials

cred = credentials.Certificate("path/to/serviceAccountKey.json")
firebase_admin.initialize_app(cred)

bot = commands.Bot(command_prefix=commands.when_mentioned_or(">>"))


@bot.event
async def on_ready():
    print("Bot loaded with name {0.user}".format(bot))


# @bot.event
# async def on_message(_message):
#     if _message.reference is not None and not _message.is_system():
#         print("1")
#         await bot.http.delete_message(_message.reference.channel_id, _message.reference.message_id)
#         print("awaited")
#         _message.delete()

@bot.command()
async def my_id(ctx, *arg):
    embed = discord.Embed()
    embed.title = "Your id is {0}".format(ctx.author.id)
    await ctx.message.reply(embed=embed)


@bot.command()
async def send_embed(ctx, *args):
    embed = discord.Embed()
    channel = ctx.channel
    for _input in args:
        splitted = _input.split(" ")

        for _i, _s in enumerate(splitted):
            if _s[-1] == '\\' and _i < len(splitted):
                splitted[_i : _i+1] = [''.join(splitted[_i : _i+1])]

        print(str(splitted))

        if len(splitted) > 1:
            prop = splitted[0]
            context = ' '.join(splitted[1:len(splitted)])
            match prop:
                case 'channel':
                    new_channel = await bot.fetch_channel(channel_id=context)
                    if new_channel is not None:
                        channel = new_channel
                case 'author':
                    try:
                        author = await bot.fetch_user(user_id=int(context))
                        if author is not None:
                            embed.set_author(name=author.name, icon_url=author.avatar_url)
                    except ValueError:
                        await ctx.message.reply("Author ID provided is invalid.")
                case 'authorName':
                    embed.set_author(name=context)
                case 'title':
                    embed.title = context
                case 'desc':
                    embed.description = context

    await ctx.message.delete()
    await channel.send(embed=embed)

bot.run(os.getenv('TOKEN'))


import os
import discord
from discord.ext import commands

bot = commands.Bot(command_prefix=commands.when_mentioned_or(">>"))

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

cred = credentials.Certificate('./fantasy-rp-9dd00.json')
firebase_admin.initialize_app(cred)

database = firestore.client()

receiving_char_channelID = 987191573764800512
list_char_channelID = 987191597038981171

@bot.command()
async def my_id(ctx, *arg):
    embed = discord.Embed()
    embed.title = "Your id is {0}".format(ctx.author.id)
    await ctx.message.reply(embed=embed)

@bot.command()
async def send_embed(ctx, *args):
    embed = discord.Embed()
    channel = ctx.channel

    await embed_edit(embed, args)

    await ctx.message.delete()
    await channel.send(embed=embed)

@bot.command()
async def clear(ctx, *args):
    try:
        async for message in ctx.channel.history():
            try:
                await message.delete()
            except:
                print("Error in clear one message.")
    except:
        ctx.message.reply("Unable to execute command in this channel.")

@bot.command()
async def show_edit(ctx, *args):
    message = ctx.message
    if message.reference is not None and not message.is_system():
        try:
            reference_msg = message.reference.resolved
            if len(reference_msg.embeds) > 0:
                embed = reference_msg.embeds[0]
                embed_dict = embed.to_dict()
                reply_string = ""
                for key, value in embed_dict.items():
                    reply_string += "{0}:\n```{1}```\n".format(key, value)

                await message.reply(reply_string)
        except:
            await message.reply("Failure")

@bot.command()
async def edit(ctx, *args):
    message = ctx.message
    if message.reference is not None and not message.is_system():
        try:
            reference_msg = message.reference.resolved
            if len(reference_msg.embeds) > 0:
                embed = reference_msg.embeds[0]
                await embed_edit(embed, args)
                await message.delete()
                await reference_msg.edit(embed=embed)
        except:
            await message.reply("Failure")

@bot.event
async def on_ready():
    print("Bot loaded with name {0.user}".format(bot))

@bot.event
async def on_message(_message):
    if _message.author.id != 634873409393917952:
        return

    await bot.process_commands(_message)

    # accepting characters
    if _message.channel.id == receiving_char_channelID:
        character_name = ''
        author_id = _message.author.id
        if len(_message.embeds) == 0: # submission is done in Message
            content = _message.content.casefold()
            a_ = content.split('name:')
            if len(a_) > 1:
                try:
                    character_name = a_[1].split('\n')[0]
                except:
                    character_name = 'new character'

        else: # submission is done in Google Doc
            character_name = _message.embeds[0].title

        # new character is successfully added
        if character_name != '':
            await _message.reply("Your character is saved under the name of '{0}'".format(character_name))
            snapshot = database.collection('User').document(str(author_id)).get()
            list_channel = await bot.fetch_channel(channel_id=list_char_channelID)
            new_character = {
                'name': character_name,
                'url': _message.jump_url,
            }
            # first character
            if not snapshot.exists:
                array = [new_character]
                embed = await create_character_list_embed(authorID=author_id, char_array=array)
                list_message = await list_channel.send(embed=embed)
                database.collection('User').document(str(author_id)).set({
                    "character_list_messageID": list_message.id,
                    "characters": array
                })
            else:
                data = snapshot.to_dict()
                data['characters'].append(new_character)
                list_message = await list_channel.fetch_message(data['character_list_messageID'])
                embed = await create_character_list_embed(authorID=author_id, char_array=data['characters'])
                if list_message is None:
                    new_list_message = await list_channel.send(embed=embed)
                    data['character_list_messageID'] = new_list_message.id
                else:
                    await list_message.edit(embed=embed)
                database.collection('User').document(str(author_id)).update(data)

    # delete message
    # if _message.reference is not None and not _message.is_system():
    #     await bot.http.delete_message(_message.reference.channel_id, _message.reference.message_id)
    #     _message.delete()

async def create_character_list_embed(authorID, char_array):
    user = await bot.fetch_user(user_id=authorID)
    embed = discord.Embed()
    embed.set_author(name=user.name, icon_url=user.avatar_url)
    desc_string = '( empty )'
    for char_info in char_array:
        if desc_string == '( empty )':
            desc_string = ''
        arr = [word for word in char_info.get('name').split(" ") if len(word) > 0]
        name = " ".join(arr).title()
        desc_string += "[{0}]({1})\n".format(name, char_info.get('url'))
    embed.description = desc_string
    return embed

async def embed_edit(_embed, args):
    embed = _embed
    author_name = ""
    author_url = ""

    for _input in args:
        splitted = _input.split(" ")
        if len(splitted) > 1:
            prop = splitted[0]
            context = ' '.join(splitted[1:len(splitted)])
            print("{0}: {1}".format(prop, context))
            match prop:
                case 'thumbnail':
                    embed.set_thumbnail(url=context)
                case 'image':
                    embed.set_image(url=context)
                case 'channel':
                    new_channel = await bot.fetch_channel(channel_id=context)
                    if new_channel is not None:
                        channel = new_channel
                case 'author':
                    try:
                        author = await bot.fetch_user(user_id=int(context))
                        print(author)
                        if author is not None:
                            author_name = author.name
                            author_url = author.avatar_url
                    except ValueError:
                        print(ValueError)
                case 'author_url':
                    author_url = context
                case 'author_name':
                    author_name = context
                case 'title':
                    embed.title = context
                case 'desc':
                    embed.description = context

    embed.set_author(name=author_name, icon_url=author_url)

bot.run(os.getenv('TOKEN'))


import os
import random
from typing import List, Tuple

import discord
from discord.ext import commands

bot = commands.Bot(command_prefix=">>")

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

cred = credentials.Certificate('./fantasy-rp-9dd00.json')
firebase_admin.initialize_app(cred)

database = firestore.client()

receiving_char_channelID = 987191573764800512
list_char_channelID = 987191597038981171
listening_channels = []

# bot commands
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


SYMBOLS = ['♠', '♥', '♦', '♣']
DICTATOR = {
    "spade": '♠',
    "heart": '♥',
    "diamond": '♦',
    "club": '♣'
}

class Deck:
    def __init__(self):
        self.array: List[Tuple] = [(s, n) for s in SYMBOLS for n in range(0, 5)]
        self.array_L = 4 * 5
        random.shuffle(self.array)

    def draw(self, _count=1):
        if self.array_L - _count >= 0:
            array = []
            for _ in range(_count):
                array.append(self.array.pop())
                self.array_L -= 1
            return array
        else:
            return None

@bot.command()
async def start_game(ctx, *args):
    async def update_player(_player):
        embed = discord.Embed()
        description = "Hand: \n"

        for card in _player['hand']:
            description += f'`[{card[0]} {card[1]}]`\n'

        description += "CB: \n"
        for card in _player['cb']:
            description += f'`[{card[0]} {card[1]}]`\n'

        await embed_edit(embed, [
            f'title {"❤" * (_player["HP"] // 100)}',
            f'author {_player["pid"]}',
            f'desc {description}',
            f'footer_name Quadrant: {_player["quadrant"]}'
        ])

        try:
            await _player['message'].edit(embed=embed)
        except KeyError:
            _player['message'] = await ctx.channel.send(embed=embed)

    deck = Deck()
    player_count = len(ctx.message.mentions)
    player_array = list(map(lambda u: {
        'pid': f'{u.id}',
        'name': u.name,
        'HP': 400,
        'hand': deck.draw(4),
        'cb': [],
        'quadrant': random.randint(1, 4)
    }, ctx.message.mentions))

    print(f'Player Count: {player_count}')

    random.shuffle(player_array)

    # announce information and begin
    deck_embed = discord.Embed(title=f"Deck has {deck.array_L} cards left.")
    deck_mes = await ctx.channel.send(embed=deck_embed)

    # player embeds
    for player in player_array:
        await update_player(player)

    # while loop
    index = 0
    command = ''
    def skip_turn(): command == 'next' or command == 'end' or command == 'round'
    player = player_array[index]
    while command != 'end':
        # announce who goes
        await embed_edit(deck_embed, [
            f"title Deck has {deck.array_L} cards left.",
            f"footer_name {player['name']} goes..."
        ])
        await deck_mes.edit(embed=deck_embed)

        # listen to commands
        while not skip_turn():
            print("Waiting for command.")
            command_mes = await bot.wait_for('message', check=lambda m: m.channel.id == ctx.message.channel.id)
            c_args = command_mes.content.split(" ")
            command = c_args[0]
            args = c_args[1::]

            # special commands
            if skip_turn():
                if command == 'round':
                    player['hand'].append(deck.draw())
                continue

            # find player
            player_targeted = None
            try:
                player_targeted = next(p for p in player_array if p['pid'] == args[0] or p['name'] == args[0].lower())
            except IndexError:
                print("Did not provide Player")
                continue
            except StopIteration:
                print("Player cannot be found.")
                continue

            # deal with command
            match command:
                # status [name] [duration]
                case 'status':
                    try:
                        name = args[1]
                        duration = int(args[2])
                    except:
                        print("Unknown error")

                # cb [sym] [#]
                case 'cb':
                    try:
                        chant_card_id = player['hand'].index((DICTATOR[args[1]], int(args[2])))
                        player['cb'].append(player['hand'][chant_card_id])
                        del player['hand'][chant_card_id]
                    except KeyError as ke:
                        print(ke)
                    except ValueError as ve:
                        print(ve)

                # cast [sym] [#]
                case 'cast':
                    try:
                        spell_card_id = player['cb'].index((DICTATOR[args[1]], int(args[2])))
                        del player['cb'][spell_card_id]
                    except:
                        print("Unknown error")

                # quadrant [#]
                case 'quadrant':
                    try:
                        quadrant = max(1, min(4, int(args[1])))
                        player_targeted['quadrant'] = quadrant
                    except:
                        print("Unknown error")

                # hp [add value]
                case 'hp':
                    try:
                        player_targeted['HP'] += int(args[1])
                    except ValueError:
                        print("HP value is not valid.")
                    except IndexError:
                        print("Not enough arguments")
                    except:
                        print("Unknown error")

            for player in player_array:
                await update_player(player)

        if command == 'end':
            break

        # reduce Status round count
        index = (index + 1) % player_count
        player = player_array[index]
        command = ''


# bot events
@bot.event
async def on_ready():
    print(f"Bot loaded with name {bot.user}")


@bot.event
async def on_message(_message):
    if _message.author.id == 634873409393917952:
        await bot.process_commands(_message)

    # accepting characters
    if _message.channel.id == receiving_char_channelID:
        character_name = ''
        author_id = _message.author.id
        if len(_message.embeds) == 0:  # submission is done in Message
            content = _message.content.casefold()
            a_ = content.split('name:')
            if len(a_) > 1:
                try:
                    character_name = a_[1].split('\n')[0]
                except:
                    character_name = 'new character'

        else:  # submission is done in Google Doc
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

    # listening to message
    # for (channel_id, count, array) in listening_channels:
    #     if _message.channel.id == channel_id:
    #         count -= 1
    #         array.append(_message)
    #         if count == 0:
    #             # fin


# functions
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
    footer_name = ""
    footer_url = ""

    for _input in args:
        splitted = _input.split(" ")
        if len(splitted) > 1:
            prop = splitted[0]
            context = ' '.join(splitted[1:len(splitted)])
            print("{0}: {1}".format(prop, context))
            match prop:
                case 'footer_name':
                    footer_name = context
                case 'footer_url':
                    footer_url = context
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
    embed.set_footer(text=footer_name, icon_url=footer_url)


# async def listen_to_message(_channel, _count):
#     # send request to event
#     returning_mes_array = []
#     listening_channels.append((_channel.id, _count, returning_mes_array))
#     # wait for request to finish
#     # return messages

bot.run(os.getenv('TOKEN'))

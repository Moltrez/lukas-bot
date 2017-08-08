import random, os, re
from PIL import Image
from image_process import resize_and_crop
from discord.ext import commands as bot

background_path = './selfie/backgrounds/'


class Chat:
    """I'm always up for a conversation."""

    def __init__(self, bot):
        self.bot = bot

    @bot.command()
    async def hi(self):
        """Allow me to tell you a bit about myself."""
        quotes = ["I like to lose myself in the books when I can. It should be no surprise. Even I like a good escape.",
                  "Some may find this surprising, but I am a fan of sweets. When I have a sweet cookie or a spoonful of honey, it's like all my fatigue is blown away!",
                  "I am of a noble family... at least in the world where I am from. Our home is near the border, so I joined the Deliverance when crisis erupted in our lands."]
        await self.bot.say(random.choice(quotes))

    @bot.command()
    async def where(self):
        """I will tell you where I have been."""
        await self.bot.say("I have taken selfies at these locations:\n" + "```" + "\n".join(
            [a[:-4] for a in os.listdir(background_path)]) + "```")

    @bot.command()
    async def selfie(self, *args):
        """Please type `!help selfie` for more information.
        I have travelled to many places and have many photos to share with you. Ask me for a random one or specify a location I've been to.
        Usage: selfie (\"location\")"""
        selfie_path = './selfie/made/'

        requested = args
        background_files = []
        backgrounds = {a.lower(): a for a in os.listdir(background_path)}
        if len(requested) == 0:
            background_files = [random.choice([a for a in backgrounds.values()])]
        else:
            for request in requested:
                file_extension_or_not_pattern = re.compile('(\.[a-z]+)?$', re.I | re.M)
                found = False
                for extension in ['.png', '.jpg']:
                    request_file = file_extension_or_not_pattern.sub(extension, request).lower()
                    if request_file in backgrounds:
                        background_files.append(backgrounds[request_file])
                        found = True
                if not found:
                    await self.bot.say('I have not been to ' + request + '.')
                    await self.bot.say(
                        'If the location is multiple words, please group it within quotes, such as `"mountain trail"`.')

        for background_file in background_files:
            await self.bot.say("Ah yes, here I am at the " + background_file[:-3])
            if not os.path.exists(selfie_path + background_file):
                background = resize_and_crop(background_path + background_file, (500, 500))
                foreground = Image.open('./selfie/lukas.png')
                background.paste(foreground, (0, 0), foreground)
                background.save(selfie_path + background_file, "PNG")
            await self.bot.upload(selfie_path + background_file)


def setup(bot):
    bot.add_cog(Chat(bot))

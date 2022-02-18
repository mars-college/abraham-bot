import datetime
import random
from ssl import CHANNEL_BINDING_TYPES
import discord
from discord.ext import commands
from marsbots_core.models import ChatMessage
from marsbots_core.programs.lm import complete_text
from marsbots_core.resources.language_models import OpenAIGPT3LanguageModel
from marsbots_core.resources.discord_utils import (
    get_discord_messages,
    is_mentioned,
    replace_bot_mention,
    replace_mentions_with_usernames,
)
from . import (
    prompts,
    channels
)


def get_nick(obj):
    if hasattr(obj, "nick") and obj.nick is not None:
        return obj.nick
    else:
        return obj.name

class AbrahamCog(commands.Cog):
    def __init__(self, bot: commands.bot) -> None:
        self.bot = bot
        self.language_model = OpenAIGPT3LanguageModel(
            engine="davinci",
            temperature=0.9,
            frequency_penalty=0.15,
            presence_penalty=0.01,
        )

    @commands.Cog.listener("on_message")
    async def on_message(self, message: discord.Message) -> None:
        dm = isinstance(message.channel, discord.channel.DMChannel)
        dm_allowed = dm and message.author.id in channels.DM_ALLOWED_USERS
        if (
            is_mentioned(message, self.bot.user)
            and message.author.id != self.bot.user.id
            and (dm_allowed or message.channel.id in channels.ALLOWED_CHANNELS)
        ):
            ctx = await self.bot.get_context(message)
            last_messages = await get_discord_messages(
                ctx.channel, limit=6, after=datetime.timedelta(minutes=20)
            )
            async with ctx.channel.typing():
                prompt = self.format_prompt(last_messages)
                #print(f'=============\nprompt\n{prompt}=============\n')
                completion = await complete_text(
                    self.language_model, prompt, max_tokens=250, stop=["<", "\n", "**["], use_content_filter=True
                )
                print(f'=============\ncompletion\n{completion}=============\n')
                await message.reply(completion.strip())

    def format_prompt(self, messages):
        last_message_content = replace_bot_mention(messages[-1].content).strip()
        messages_content = self.format_messages(messages)
        topic_idx = self.get_similar_topic_idx(last_message_content)
        topic_prelude = prompts.topics[topic_idx]["prelude"]
        print("=============")
        print(f' -> last message: {last_message_content}')
        print(f' -> search result: {prompts.topics[topic_idx]["document"]}')
        prompt = (
            self.format_prompt_messages(prompts.prelude)
            + "\n"
            + self.format_prompt_messages(topic_prelude)
            + "\n"
            + messages_content
            + "\n"
            + "**["+self.bot.user.name+"]**:"
        )
        return prompt

    def format_prompt_messages(self, messages):
        return "\n".join(
            ["**[%s]**: %s"%(message['sender'], message['message']) for message in messages]
        )

    def format_messages(self, messages_content):
        return "\n".join(
            [
                str(
                    ChatMessage(
                        self.message_preprocessor(message_content),
                        self.get_sender(message_content),
                        deliniator_left="**[",
                        deliniator_right="]**:",
                    )
                )
                for message_content in messages_content
            ]
        )

    def get_similar_topic_idx(self, query: str) -> int:
        docs = [topic["document"] for topic in prompts.topics]
        res = self.language_model.document_search(docs, query)
        return self.language_model.most_similar_doc_idx(res)

    def message_preprocessor(self, message: discord.Message) -> str:
        message_content = replace_bot_mention(message.content, only_first=True)
        message_content = replace_mentions_with_usernames(
            message_content, message.mentions
        )
        message_content = message_content.strip()
        return message_content

    def get_sender(self, message: discord.Message) -> str:
        if message.author.id == self.bot.user.id:
            return self.bot.user.name
        else:
            return f"{get_nick(message.author)}"


def setup(bot: commands.Bot) -> None:
    bot.add_cog(AbrahamCog(bot))

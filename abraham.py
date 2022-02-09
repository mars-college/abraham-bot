import datetime
import random
import discord
from discord.ext import commands
from marsbots_core.models import ChatMessage
from marsbots_core.programs.lm import complete_text
from marsbots_core.resources.discord_utils import (
    get_discord_messages,
    is_mentioned,
    replace_bot_mention,
    replace_mentions_with_usernames,
)

from marsbots_core.resources.language_models import OpenAIGPT3LanguageModel

from . import prompts


class AbrahamCog(commands.Cog):
    def __init__(self, bot: commands.bot) -> None:
        self.bot = bot
        self.language_model = OpenAIGPT3LanguageModel(
            engine="curie",
            temperature=0.9,
            frequency_penalty=0.15,
            presence_penalty=0.01,
        )

    @commands.Cog.listener("on_message")
    async def on_message(self, message: discord.Message) -> None:
        if is_mentioned(message, self.bot.user):
            ctx = await self.bot.get_context(message)
            last_messages = await get_discord_messages(
                ctx.channel, limit=8, after=datetime.timedelta(hours=1)
            )
            async with ctx.channel.typing():
                prompt = self.format_prompt(last_messages)
                print(prompt)
                completion = await complete_text(
                    self.language_model, prompt, max_tokens=250, stop=["<", "\n"]
                )
                await message.reply(completion)

    def format_prompt(self, messages):
        messages_content = self.format_messages(messages)
        last_message_content = messages_content[-1]
        topic_idx = self.get_similar_topic_idx(last_message_content)
        topic_prelude = prompts.topics[topic_idx]["prelude"]
        prompt = (
            prompts.intro
            + "\n\n"
            + self.format_prompt_messages(prompts.prelude)
            + "\n"
            + self.format_prompt_messages(topic_prelude)
            + "\n"
            + messages_content
            + "\n"
            + "<S>"
        )
        return prompt

    def format_prompt_messages(self, messages):
        return "\n".join(
            [f"{message['sender']} {message['message']}" for message in messages]
        )

    def format_messages(self, messages_content):
        return "\n".join(
            [
                str(
                    ChatMessage(
                        self.message_preprocessor(message_content),
                        self.get_sender(message_content),
                        deliniator_left="<",
                        deliniator_right=">",
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
            return "S"
        else:
            return f"P{random.randint(1, 4)}"


def setup(bot: commands.Bot) -> None:
    bot.add_cog(AbrahamCog(bot))

import discord
from discord.ext import commands
from marsbots_core.models import ChatMessage
from marsbots_core.programs.lm import complete_text
from marsbots_core.resources.discord_utils import (
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

    @commands.command()
    async def search(self, ctx, *query):
        query = " ".join(query)
        docs = [topic["document"] for topic in prompts.topics]
        res = self.language_model.document_search(docs, query)
        most_similar_idx = self.language_model.most_similar_doc_idx(res)
        doc = prompts.topics[most_similar_idx]["document"]
        await ctx.send(f"The most similar prompt is: {doc}")

    @commands.command()
    async def similarity(self, ctx, *query):
        query = " ".join(query)
        doc = "What do you see as the future of AI art?"
        res = self.language_model.document_similarity(doc, query)
        await ctx.send("My question was: " + doc)
        await ctx.send("Your answer's similarity is: " + str(res))

    @commands.Cog.listener("on_message")
    async def on_message(self, message: discord.Message) -> None:
        if is_mentioned(message, self.bot.user):
            ctx = await self.bot.get_context(message)
            async with ctx.channel.typing():
                prompt = self.format_prompt(message)
                print(prompt)
                completion = await complete_text(
                    self.language_model, prompt, max_tokens=250, stop=["<", "\n"]
                )
                await message.reply(completion)

    def format_prompt(self, message):
        message_content = replace_bot_mention(
            message.content, only_first=True, replacement_str="<S>"
        )
        message_content = replace_mentions_with_usernames(
            message_content, message.mentions
        )
        message_content = message_content.strip()
        topic_idx = self.get_similar_topic_idx(message_content)
        topic_prelude = prompts.topics[topic_idx]["prelude"]
        last_message = str(
            ChatMessage(
                message_content, "P4", deliniator_left="<", deliniator_right=">"
            )
        )
        prompt = (
            self.format_prompt_messages(prompts.prelude)
            + "\n"
            + self.format_prompt_messages(topic_prelude)
            + "\n"
            + last_message
            + "\n"
            + "<S>"
        )
        return prompt

    def format_prompt_messages(self, messages):
        return "\n".join(
            [f"{message['sender']} {message['message']}" for message in messages]
        )

    def get_similar_topic_idx(self, query: str) -> int:
        docs = [topic["document"] for topic in prompts.topics]
        res = self.language_model.document_search(docs, query)
        return self.language_model.most_similar_doc_idx(res)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(AbrahamCog(bot))

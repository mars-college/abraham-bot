import discord
from discord.ext import commands
from marsbots_core.resources.discord_utils import is_mentioned, process_mention_as_command

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
            await process_mention_as_command(
                ctx,
                self,
                "I'm sorry, I don't understand you",
            )


def setup(bot: commands.Bot) -> None:
    bot.add_cog(AbrahamCog(bot))

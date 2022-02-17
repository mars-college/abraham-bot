module.exports = {
  apps: [
    {
      name: "abraham",
      script: "../../bot.py",
      interpreter: "python",
      args: "./abraham.json --cog-path=bots.abraham-bot.abraham --dotenv-path=.env",
      watch: ["."],
      ignore_watch: ["__pycache__", "*.pyc"],
      watch_delay: 1000
    },
  ],
};

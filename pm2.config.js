module.exports = {
  apps: [
    {
      name: "clip_art",
      script: "../../../../bot.py",
      interpreter: "python",
      args: "./clip_art.json --cog-path=bots.marsbots.2022.clip_art.clip_art --dotenv-path=.env",
      watch: ["."],
      ignore_watch: ["__pycache__", "*.pyc"],
      watch_delay: 1000
    },
  ],
};

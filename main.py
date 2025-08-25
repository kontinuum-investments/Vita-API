from typing import Dict

from fastapi import FastAPI

from tools import discord

app = FastAPI()
app.include_router(discord.router, prefix="/discord")

if __name__ == "__main__":
    import uvicorn
    from dotenv import load_dotenv

    load_dotenv()
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

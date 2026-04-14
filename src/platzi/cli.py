import asyncio
from pathlib import Path
from typing import Optional

import typer
from rich import print
from typing_extensions import Annotated

from platzi import AsyncPlatzi, Cache

from .models import Quality
from .utils import validate_course_url

app = typer.Typer(rich_markup_mode="rich")


@app.command()
def login():
    """
    Open a browser window to Login to Platzi.

    Usage:
        platzi login
    """
    asyncio.run(_login())


@app.command()
def logout():
    """
    Delete the Platzi session from the local storage.

    Usage:
        platzi logout
    """
    asyncio.run(_logout())


@app.command()
def set_cookies(
    path: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=True,
            dir_okay=False,
            help="Path to cookies.json",
            show_default=False,
        ),
    ],
):
    """
    Login to Platzi using your cookies.

    Usage:
        platzi set-cookies cookies.json
    """
    asyncio.run(_set_cookies(path))


async def _set_cookies(path: Path):
    """Load cookies from file and save state inside an AsyncPlatzi context."""
    async with AsyncPlatzi() as platzi:
        await platzi.set_cookies(path)


@app.command()
def download(
    url: Annotated[
        Optional[str],
        typer.Argument(
            help="The URL of the course to download",
            show_default=False,
        ),
    ] = None,
    quality: Annotated[
        Quality,
        typer.Option(
            "--quality",
            "-q",
            help="The quality of the video to download.",
            show_default=True,
        ),
    ] = Quality.P720,
    overwrite: Annotated[
        bool,
        typer.Option(
            "--overwrite",
            "-w",
            help="Overwrite files if exist.",
            show_default=True,
        ),
    ] = False,
    file: Annotated[
        Optional[str],
        typer.Option(
            "--file",
            "-f",
            help="Path to a text file containing one course URL per line.",
            show_default=False,
        ),
    ] = None,
    headless: Annotated[
        bool,
        typer.Option(
            "--headless/--no-headless",
            help="Run the browser hidden (--headless: default) or visible (--no-headless).",
            show_default=True,
        ),
    ] = True,
):
    """
    Download a Platzi course from the given URL, or multiple from a text file.

    Arguments:
        url: str - The URL of the course to download (optional if --file is used).

    Usage:
        platzi download <url>

    Example:
        platzi download https://platzi.com/cursos/python/
        platzi download --file courses_links.txt
    """

    urls = []

    if file:
        try:
            with open(file, "r", encoding="utf-8") as f:
                urls = [validate_course_url(line.strip()) for line in f if line.strip()]
        except FileNotFoundError:
            print(f"[red]Error:[/red] The file '{file}' does not exist.")
            raise typer.Exit(code=1)
        except ValueError as e:
            print(f"[red]Error:[/red] {e}")
            raise typer.Exit(code=1)
    elif url:
        urls = [validate_course_url(url)]
    else:
        print("[red]Error:[/red] You must specify a URL or use --file.")
        raise typer.Exit(code=1)

    asyncio.run(
        _download(urls, quality=quality, overwrite=overwrite, headless=headless)
    )


@app.command()
def clear_cache():
    """
    Clear the Platzi CLI cache.

    Usage:
        platzi clear-cache
    """
    Cache.clear()
    print("[green]Cache cleared successfully 🗑️[/green]")


async def _login():
    # Force the login to ALWAYS show the browser
    async with AsyncPlatzi(headless=False) as platzi:
        await platzi.login()


async def _logout():
    async with AsyncPlatzi() as platzi:
        await platzi.logout()


async def _download(urls: list[str], **kwargs):
    headless = kwargs.pop("headless", True)
    async with AsyncPlatzi(headless=headless) as platzi:
        for url in urls:
            try:
                await platzi.download(url, **kwargs)
            except Exception as e:
                print(f"[red]Error downloading {url}:[/red] {str(e)}")

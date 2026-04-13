import functools
import json
import os
import time
from pathlib import Path
from urllib.parse import unquote

import aiofiles
from playwright.async_api import BrowserContext, Page, async_playwright
from rich import box, print
from rich.console import Console
from rich.live import Live
from rich.table import Table

from .collectors import (
    get_course_metadata,
    get_course_title,
    get_draft_chapters,
    get_unit,
)
from .constants import LOGIN_DETAILS_URL, LOGIN_URL, SESSION_FILE
from .helpers import read_json, write_json
from .logger import Logger
from .m3u8 import m3u8_dl
from .models import TypeUnit, User
from .utils import (
    clean_string,
    dismiss_modals,
    download,
    ensure_filename_length,
    normalize_cookies,
    progressive_scroll,
)

GOTO_TIMEOUT = 90_000  # ms — Platzi pages can be slow


def login_required(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        self = args[0]
        if not isinstance(self, AsyncPlatzi):
            Logger.error(f"{login_required.__name__} can only decorate Platzi class.")
            return
        if not self.loggedin:
            Logger.error("Login first!")
            return
        return await func(*args, **kwargs)

    return wrapper


def try_except_request(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        self = args[0]
        if not isinstance(self, AsyncPlatzi):
            Logger.error(
                f"{try_except_request.__name__} can only decorate Platzi class."
            )
            return

        try:
            return await func(*args, **kwargs)
        except Exception as e:
            if str(e):
                Logger.error(e)
        return

    return wrapper


class AsyncPlatzi:
    def __init__(self, headless=True):
        self.loggedin = False
        self.headless = headless
        self.user = None

    async def get_json(self, url: str) -> dict:
        page = await self.page
        await page.goto(url, timeout=GOTO_TIMEOUT, wait_until="domcontentloaded")
        try:
            content = await page.locator("pre").first.text_content(timeout=5_000)
        except Exception:
            content = await page.evaluate("() => document.body.innerText")
        await page.close()
        return json.loads(content or "{}")

    async def __aenter__(self):
        self._playwright = await async_playwright().start()
        # --no-focus-on-startup evita que la ventana robe el foco al abrirse
        launch_args = ["--no-focus-on-startup", "--disable-focus-on-page-show"]
        self._browser = await self._playwright.chromium.launch(
            headless=self.headless,
            args=launch_args,
        )
        self._context = await self._browser.new_context(
            java_script_enabled=True,
            is_mobile=True,
        )

        try:
            await self._load_state()
        except Exception:
            pass

        await self._set_profile()

        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self._context.close()
        await self._browser.close()
        await self._playwright.stop()

    @property
    async def page(self) -> Page:
        return await self._context.new_page()

    @property
    def context(self) -> BrowserContext:
        return self._context

    @try_except_request
    async def _set_profile(self) -> None:
        import rnet

        try:
            # Usar las cookies guardadas directamente via HTTP — no depende del browser
            cookies = await self.context.cookies()
            cookie_header = "; ".join(f"{c['name']}={c['value']}" for c in cookies)

            client = rnet.Client(impersonate=rnet.Impersonate.Firefox139)
            response = await client.get(
                LOGIN_DETAILS_URL,
                headers={
                    "Cookie": cookie_header,
                    "Referer": "https://platzi.com/",
                    "Accept": "application/json",
                },
            )
            data = await response.json()
            await response.close()
            self.user = User(**data)
        except Exception:
            return

        if self.user.is_authenticated:
            self.loggedin = True
            Logger.info(f"Hi, {self.user.username}!\n")

    @try_except_request
    async def login(self) -> None:
        Logger.info("Please login, in the opened browser")
        Logger.info("You have to login manually, you have 2 minutes to do it")

        page = await self.page
        await page.goto(LOGIN_URL, timeout=GOTO_TIMEOUT, wait_until="domcontentloaded")
        try:
            avatar = await page.wait_for_selector(
                ".styles-module_Menu__Avatar__FTuh-",
                timeout=2 * 60 * 1000,
            )
            if avatar:
                self.loggedin = True
                await self._save_state()
                Logger.info("Logged in successfully")
        except Exception:
            raise Exception("Login failed")
        finally:
            await page.close()

    @try_except_request
    async def logout(self):
        SESSION_FILE.unlink(missing_ok=True)
        Logger.info("Logged out successfully")

    @try_except_request
    async def set_cookies(self, path: Path) -> None:
        """
        Load cookies from a JSON file and set them in the browser context.
        Marks the client as authenticated if the cookies are valid. Saves state
        """
        try:
            cookies = read_json(str(path))

            if not isinstance(cookies, list):
                Logger.error("The JSON file must contain a list of cookies.")
                return

            cleaned_cookies = normalize_cookies(cookies)

            await self.context.add_cookies(cleaned_cookies)

            await self._set_profile()

            if self.loggedin:
                await self._save_state()
                Logger.info("Cookies imported, Logged in successfully!\n")
            else:
                Logger.error(
                    "Login failed. The cookies provided may be invalid or expired."
                )

        except Exception as e:
            Logger.error(f"Error processing cookie file: {e}")

    @try_except_request
    @login_required
    async def download(self, url: str, **kwargs):
        page = await self.page
        await page.goto(url, timeout=GOTO_TIMEOUT, wait_until="domcontentloaded")

        # course title
        course_title = await get_course_title(page)

        # download directory
        DL_DIR = Path("Courses") / clean_string(course_title)
        DL_DIR.mkdir(parents=True, exist_ok=True)

        metadata = await get_course_metadata(page)

        cover_url = metadata.get("cover_image_url")
        if cover_url:
            ext = cover_url.split(".")[-1].split("?")[0]
            file_path = DL_DIR / f"cover.{ext}"
            await download(cover_url, file_path)

        pub_date = metadata.get("publication_date")
        if pub_date:
            file_path = DL_DIR / f"{pub_date}.txt"
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(pub_date)

        # save page as mhtml
        presentation_path = DL_DIR / "presentation.mhtml"
        await self.save_page(page, path=presentation_path, **kwargs)

        # iterate over chapters
        draft_chapters = await get_draft_chapters(page)

        # --- Course Details Table ---
        table = Table(
            title=course_title,
            caption="processing...",
            caption_style="green",
            title_style="green",
            header_style="green",
            footer_style="green",
            show_footer=True,
            box=box.ROUNDED,
        )
        table.add_column("Sections", style="green", footer="Total", no_wrap=True)
        table.add_column("Lessons", style="green", footer="0", justify="center")

        total_units = 0

        with Live(table, refresh_per_second=4):
            for idx, section in enumerate(draft_chapters, 1):
                time.sleep(0.3)
                num_units = len(section.units)
                total_units += num_units
                table.add_row(f"{idx}-{section.name}", str(len(section.units)))
                table.columns[1].footer = str(total_units)

        for idx, draft_chapter in enumerate(draft_chapters, 1):
            Logger.info(f"Creating directory: {draft_chapter.name}")

            CHAP_DIR = DL_DIR / f"{idx:02}-{clean_string(draft_chapter.name)}"
            CHAP_DIR.mkdir(parents=True, exist_ok=True)

            for jdx, draft_unit in enumerate(draft_chapter.units, 1):
                try:
                    unit = await get_unit(self.context, draft_unit.url)
                except Exception as e:
                    Logger.error(f"Skipping unit [{jdx}] {draft_unit.url} — {e}")
                    continue
                file_name = f"{jdx:02}-{clean_string(unit.title)}"
                file_name = ensure_filename_length(file_name, CHAP_DIR)

                # download video
                if unit.video:
                    dst = CHAP_DIR / f"{file_name}.mp4"
                    Logger.print(f"[{dst.name}]", "[DOWNLOADING-VIDEO]")
                    await m3u8_dl(unit.video.url, dst, **kwargs)

                    subs = unit.video.subtitles_url
                    if subs:
                        for i, sub in enumerate(subs):
                            s = sub.lower()
                            lang = (
                                "es"
                                if "es" in s
                                else "en"
                                if "en" in s
                                else "pt"
                                if "pt" in s
                                else i + 1
                            )
                            dst = CHAP_DIR / f"{file_name}_{lang}.vtt"
                            Logger.print(f"[{dst.name}]", "[DOWNLOADING-SUBS]")
                            await download(sub, dst, **kwargs)

                    if unit.resources:
                        files = unit.resources.files_url
                        if files:
                            for archive in files:
                                file_name = unquote(os.path.basename(archive))
                                ext = Path(file_name).suffix
                                file_name = ensure_filename_length(file_name, CHAP_DIR)
                                dst = CHAP_DIR / f"{jdx:02}-{file_name}{ext}"
                                Logger.print(f"[{dst.name}]", "[DOWNLOADING-FILES]")
                                await download(archive, dst)

                        readings = unit.resources.readings_url
                        if readings:
                            dst = CHAP_DIR / f"{jdx:02}-Lecturas recomendadas.txt"
                            Logger.print(f"[{dst.name}]", "[SAVING-READINGS]")
                            with open(dst, "w", encoding="utf-8") as f:
                                for lecture in readings:
                                    f.write(lecture + "\n")

                        summary = unit.resources.summary
                        if summary:
                            dst = CHAP_DIR / f"{jdx:02}-Resumen.html"
                            Logger.print(f"[{dst.name}]", "[SAVING-SUMMARY]")
                            with open(dst, "w", encoding="utf-8") as f:
                                f.write(summary)

                # download lecture
                if unit.type == TypeUnit.LECTURE:
                    dst = CHAP_DIR / f"{file_name}.mhtml"
                    Logger.print(f"[{dst.name}]", "[DOWNLOADING-LECTURE]")
                    await self.save_page(unit.url, path=dst)

                # download quiz
                if unit.type == TypeUnit.QUIZ:
                    dst = CHAP_DIR / f"{file_name}.mhtml"
                    Logger.print(f"[{dst.name}]", "[DOWNLOADING-QUIZ]")
                    await self.save_page(unit.url, path=dst)

            print("=" * 100)

    @try_except_request
    async def save_page(
        self,
        src: str | Page,
        path: str | Path = "source.mhtml",
        **kwargs,
    ):
        overwrite: bool = kwargs.get("overwrite", False)

        if not overwrite and Path(path).exists():
            return

        console = Console()
        with console.status(
            "[green]Saving page...[/]\n", spinner="bouncingBar", spinner_style="green"
        ):
            if isinstance(src, str):
                page = await self.page
                await page.goto(src, timeout=GOTO_TIMEOUT, wait_until="domcontentloaded")
            else:
                page = src

            await dismiss_modals(page)
            await progressive_scroll(page)

            try:
                client = await page.context.new_cdp_session(page)
                response = await client.send("Page.captureSnapshot")
                async with aiofiles.open(
                    path, "w", encoding="utf-8", newline="\n"
                ) as file:
                    await file.write(response["data"])
            except Exception:
                raise Exception("Error saving page as mhtml")

            if isinstance(src, str):
                await page.close()

    async def _save_state(self):
        cookies = await self.context.cookies()
        write_json(SESSION_FILE, cookies)

    async def _load_state(self):
        SESSION_FILE.touch()
        cookies = read_json(SESSION_FILE)
        await self.context.add_cookies(cookies)

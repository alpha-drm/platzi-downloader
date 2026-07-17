import asyncio
import re
import time
from urllib.parse import urljoin

from playwright.async_api import BrowserContext, Page

from .cache import Cache
from .constants import PLATZI_URL
from .logger import Logger
from .models import Chapter, Resource, TypeUnit, Unit, Video
from .utils import (
    dismiss_modals,
    download_styles,
    get_m3u8_url,
    get_subtitles_url,
    slugify,
)


@Cache.cache_async
async def get_course_title(page: Page) -> str:
    SELECTOR = "h1[class*='CourseHeader']"
    EXCEPTION_MSG = "No course title found"
    try:
        title = await page.locator(SELECTOR).first.text_content()
        if not title:
            raise Exception(EXCEPTION_MSG)
    except Exception as e:
        raise Exception(EXCEPTION_MSG) from e

    return title


@Cache.cache_async
async def get_course_metadata(page: Page):
    PUBLICATION_DATE_SELECTOR = "p[class*='CoursePublicationDetails__Date']"
    COVER_IMAGE_SELECTOR = "[property='og:image']"
    try:
        cover_locator = page.locator(COVER_IMAGE_SELECTOR)
        cover_image_url = (
            await cover_locator.get_attribute("content")
            if await cover_locator.count() > 0
            else None
        )

        publication_locator = page.locator(PUBLICATION_DATE_SELECTOR).first
        try:
            await publication_locator.wait_for(state="visible", timeout=5000)
            publication_date = await publication_locator.inner_text()
        except Exception:
            pass

        return {
            "cover_image_url": cover_image_url,
            "publication_date": publication_date.strip() if publication_date else None,
        }

    except Exception as e:
        Logger.warning(
            f"The course metadata could not be extracted. {e.__class__.__name__}: {e}"
        )
        return {
            "cover_image_url": None,
            "publication_date": None,
        }


@Cache.cache_async
async def get_draft_chapters(page: Page) -> list[Chapter]:
    SELECTOR = "section[class*='Syllabus'] article"
    EXCEPTION = Exception("No sections found")
    try:
        locator = page.locator(SELECTOR)

        chapters: list[Chapter] = []
        for i in range(await locator.count()):
            chapter_name = await locator.nth(i).locator("h3 span").first.text_content()

            if not chapter_name:
                raise EXCEPTION

            units: list[Unit] = []

            items = locator.nth(i).locator("li[id^='syllabus-material'] a")
            items_count = await items.count()

            for j in range(items_count):
                item = items.nth(j)

                unit_title = await item.locator("h3").first.text_content()
                unit_url = await item.get_attribute("href")

                if not unit_url or not unit_title:
                    raise EXCEPTION

                units.append(
                    Unit(
                        type=TypeUnit.VIDEO,
                        title=unit_title,
                        url=urljoin(PLATZI_URL, unit_url),
                        slug=slugify(unit_title),
                    )
                )

            chapters.append(
                Chapter(
                    name=chapter_name,
                    slug=slugify(chapter_name),
                    units=units,
                )
            )

    except Exception as e:
        await page.close()
        raise EXCEPTION from e

    return chapters


@Cache.cache_async
async def get_unit(context: BrowserContext, url: str) -> Unit:
    TYPE_SELECTOR = ".VideoPlayer"
    TITLE_SELECTOR = "h1[class*='MaterialCourseInfo']"
    EXCEPTION = Exception("Could not collect unit data")

    MATERIAL_CONTENT = "div[class*='page_DesktopAfterMaterial__']"
    RESOURCES_SECTION = "div[class*='FilesAndLinks_FilesAndLinks__']"
    RESOURCES_LINKS = "a[class*='FilesAndLinks_Item']"

    if "/quiz/" in url:
        return Unit(
            url=url,
            title="Quiz",
            type=TypeUnit.QUIZ,
            slug="Quiz",
        )

    page = None
    try:
        page = await context.new_page()
        await page.goto(url)

        await asyncio.sleep(5)  # delay to avoid rate limiting
        await dismiss_modals(page)  # Dismiss popups before interacting with the page

        title = await page.locator(TITLE_SELECTOR).first.text_content()

        if not title:
            raise EXCEPTION

        if not await page.locator(TYPE_SELECTOR).is_visible():
            return Unit(
                url=url,
                title=title,
                type=TypeUnit.LECTURE,
                slug=slugify(title),
            )

        # It's a video unit
        content = await page.content()
        unit_type = TypeUnit.VIDEO
        video = Video(
            url=get_m3u8_url(content),
            subtitles_url=get_subtitles_url(content),
        )

        # --- Get resources and summary ---
        html_summary = None
        file_links: list[str] = []
        readings_links: list[str] = []
        extension_pattern = re.compile(r"\.\w+$")

        time.sleep(5)

        resources_section = page.locator(RESOURCES_SECTION)
        if await resources_section.count() > 0:
            resources_links = resources_section.locator(RESOURCES_LINKS)
            for i in range(await resources_links.count()):
                link = await resources_links.nth(i).get_attribute("href")
                if extension_pattern.search(link):
                    file_links.append(link)

        time.sleep(5)

        # Get material content if it exists
        material_content = page.locator(MATERIAL_CONTENT)
        if await material_content.count() > 0:
            all_css_styles: list[str] = []

            summary_section = await material_content.evaluate("el => el.outerHTML")

            # Find all CSS selectors to include in the html_summary template
            stylesheet_links = page.locator("link[rel=stylesheet]")
            count = await stylesheet_links.count()
            for i in range(count):
                href = await stylesheet_links.nth(i).get_attribute("href")
                if href:
                    stylesheet = await download_styles(href)
                    all_css_styles.append(stylesheet)

            # Get the content of the <style>
            style_blocks = await page.query_selector_all("style")
            for style in style_blocks:
                content = await style.inner_text()
                all_css_styles.append(content)

            # Combine all styles
            styles = "\n".join(filter(None, all_css_styles))

            # HTML template
            html_summary = f"""
           <!DOCTYPE html>
            <html lang="es">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>{title}</title>
                <style>
                    {styles}
                    .general-container {{
                        margin: 20px;
                        padding: 20px;
                        box-sizing: border-box;
                    }}
                    .title-header {{
                        text-align: center;
                        color: white;
                        margin-bottom: 20px;
                    }}
                </style>
            </head>
            <body>
                <div class="general-container">
                    <h1 class="title-header">{title}</h1>
                    {summary_section}
                </div>
            </body>
            </html>"""

        return Unit(
            url=url,
            title=title,
            type=unit_type,
            video=video,
            slug=slugify(title),
            resources=Resource(
                files_url=file_links,
                readings_url=readings_links,
                summary=html_summary,
            ),
        )

    except Exception as e:
        raise EXCEPTION from e

    finally:
        if page:
            await page.close()

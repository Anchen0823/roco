from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from lxml import html


SOURCE_URL = "https://wiki.biligame.com/rocom/%E7%B2%BE%E7%81%B5%E5%9B%BE%E9%89%B4"
SOURCE_TITLE = "精灵图鉴 - 洛克王国:手游WIKI_BWIKI_哔哩哔哩"
LICENSE = "CC BY-NC-SA 4.0"


def fetch_html(url: str) -> str:
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept-Language": "zh-CN,zh;q=0.9",
        },
    )
    with urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def text_content(node: html.HtmlElement, xpath: str) -> str:
    return "".join(node.xpath(xpath)).strip()


def split_types(value: str | None) -> list[str]:
    if not value:
        return []
    return [part.strip() for part in value.split(",") if part.strip()]


def image_name_from_alt(alt: str | None) -> str | None:
    if not alt:
        return None
    for prefix in ("页面 宠物 立绘 ", "图标 宠物 属性 "):
        if alt.startswith(prefix):
            return alt[len(prefix) :]
    return alt


def strip_suffix(value: str, suffix: str) -> str:
    return value[: -len(suffix)] if value.endswith(suffix) else value


def parse_page_updated(raw_html: str) -> str | None:
    match = re.search(r"更新日期[：:]\s*(\d{4}-\d{2}-\d{2})", raw_html)
    if match:
        return match.group(1)
    text = " ".join(html.fromstring(raw_html).xpath("//text()"))
    match = re.search(r"更新日期\s*[：:]\s*(\d{4}-\d{2}-\d{2})", text)
    return match.group(1) if match else None


def parse_pets(raw_html: str) -> list[dict[str, Any]]:
    doc = html.fromstring(raw_html)
    cards = doc.xpath('//div[contains(concat(" ", normalize-space(@class), " "), " divsort ")]')
    pets: list[dict[str, Any]] = []

    for index, card in enumerate(cards, start=1):
        no = text_content(card, './/p[contains(@class, "block_1")]//span/text()')
        name = text_content(card, './/p[contains(@class, "block_2")]//span/text()')
        form = text_content(card, './/p[contains(@class, "block_3")]//span/text()') or None
        href = card.xpath('.//p[contains(@class, "block_1")]//a/@href')
        image = card.xpath('.//img[contains(@class, "rocom_prop_icon")]')
        image_src = image[0].get("src") if image else None
        image_alt = image[0].get("alt") if image else None
        attribute_icons = card.xpath('.//img[contains(@class, "rocom_pet_icon")]')
        attributes = split_types(card.get("data-param2"))
        pet_id = no[3:] if no.startswith("NO.") else no or None

        pets.append(
            {
                "index": index,
                "id": pet_id,
                "no": no,
                "name": name,
                "form": form,
                "displayName": f"{name}（{form}）" if form else name,
                "stage": card.get("data-param1") or None,
                "attributes": attributes,
                "formCategory": card.get("data-param4") or card.get("data-param5") or None,
                "hasShiny": {"是": True, "否": False}.get(card.get("data-param6") or ""),
                "wikiUrl": urljoin(SOURCE_URL, href[0]) if href else None,
                "image": {
                    "url": image_src,
                    "fileName": image_name_from_alt(image_alt),
                    "alt": image_alt,
                },
                "attributeIcons": [
                    {
                        "attribute": strip_suffix(image_name_from_alt(icon.get("alt")), ".png")
                        if image_name_from_alt(icon.get("alt"))
                        else None,
                        "url": icon.get("src"),
                        "alt": icon.get("alt"),
                    }
                    for icon in attribute_icons
                ],
            }
        )

    return pets


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, pets: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "index",
                "id",
                "no",
                "name",
                "form",
                "displayName",
                "stage",
                "attributes",
                "formCategory",
                "hasShiny",
                "wikiUrl",
                "imageUrl",
            ],
        )
        writer.writeheader()
        for pet in pets:
            writer.writerow(
                {
                    "index": pet["index"],
                    "id": pet["id"],
                    "no": pet["no"],
                    "name": pet["name"],
                    "form": pet["form"] or "",
                    "displayName": pet["displayName"],
                    "stage": pet["stage"] or "",
                    "attributes": "、".join(pet["attributes"]),
                    "formCategory": pet["formCategory"] or "",
                    "hasShiny": "" if pet["hasShiny"] is None else ("是" if pet["hasShiny"] else "否"),
                    "wikiUrl": pet["wikiUrl"] or "",
                    "imageUrl": pet["image"]["url"] or "",
                }
            )


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    pets = payload["pets"]
    rows = [
        "# 精灵图鉴",
        "",
        f"- 来源：[{SOURCE_TITLE}]({SOURCE_URL})",
        f"- 授权：{LICENSE}",
        f"- Wiki 页面更新日期：{payload['metadata'].get('sourcePageUpdated') or '未知'}",
        f"- 本地整理时间：{payload['metadata']['generatedAt']}",
        f"- 精灵条目数：{len(pets)}",
        "",
        "| 图鉴号 | 名称 | 形态 | 阶段 | 属性 | 形态类别 | 异色 |",
        "|---|---|---|---|---|---|---|",
    ]
    for pet in pets:
        rows.append(
            "| {no} | {name} | {form} | {stage} | {attributes} | {form_category} | {shiny} |".format(
                no=pet["no"] or "",
                name=pet["name"],
                form=pet["form"] or "",
                stage=pet["stage"] or "",
                attributes="、".join(pet["attributes"]),
                form_category=pet["formCategory"] or "",
                shiny="" if pet["hasShiny"] is None else ("是" if pet["hasShiny"] else "否"),
            )
        )
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Update local Roco pet index data from BWIKI.")
    parser.add_argument("--input", type=Path, help="Read an already downloaded wiki HTML file.")
    parser.add_argument("--out-dir", type=Path, default=Path("data"))
    args = parser.parse_args()

    raw_html = args.input.read_text(encoding="utf-8") if args.input else fetch_html(SOURCE_URL)
    pets = parse_pets(raw_html)
    if not pets:
        print("No pet cards found.", file=sys.stderr)
        return 1

    payload = {
        "metadata": {
            "sourceTitle": SOURCE_TITLE,
            "sourceUrl": SOURCE_URL,
            "sourcePageUpdated": parse_page_updated(raw_html),
            "license": LICENSE,
            "generatedAt": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
            "count": len(pets),
        },
        "pets": pets,
    }

    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.out_dir / "精灵图鉴.json", payload)
    write_csv(args.out_dir / "精灵图鉴.csv", pets)
    write_markdown(args.out_dir / "精灵图鉴.md", payload)
    write_json(args.out_dir / "pets.json", payload)
    write_csv(args.out_dir / "pets.csv", pets)
    write_markdown(args.out_dir / "pets.md", payload)
    print(f"Wrote {len(pets)} pet entries to {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

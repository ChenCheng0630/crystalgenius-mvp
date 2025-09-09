"""Assistant profile endpoint."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/assistant", tags=["assistant"])


PROFILE = {
    "name": "小晶",
    "avatar": "https://example.com/crystal-expert.jpg",
    "intro_short": "专注天然水晶与能量手串，按寓意与体感为你精准配搭。",
    "domains": ["天然水晶手串", "寓意/能量配对"],
    "styles": ["温柔疗愈", "专业配搭", "寓意解读"],
    "stats": {
        "monthly_sales": "2.8K+ 单",
        "gmv": "￥1.9M/月",
        "positive_rate": "99% 好评",
    },
}


@router.get("/profile")
async def get_profile() -> dict:
    """Return static profile information used on the assistant screen."""

    return PROFILE

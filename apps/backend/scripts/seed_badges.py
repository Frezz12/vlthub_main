"""Seed initial badges."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from app.core.database import async_session_factory
from app.models.badge import Badge

F11_SVG = """<svg class="w-full h-full" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="f11_stroke" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#3b82f6"/>
      <stop offset="100%" stop-color="#1d4ed8"/>
    </linearGradient>
  </defs>
  <rect x="2" y="3" width="20" height="18" rx="6" stroke="url(#f11_stroke)" stroke-width="1.5"/>
  <text x="12" y="16" text-anchor="middle" font-size="10" font-weight="bold" fill="url(#f11_stroke)" font-family="monospace">F11</text>
</svg>"""

CHECK_SVG = """<svg class="w-full h-full" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="chk_bg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#3b82f6"/>
      <stop offset="100%" stop-color="#1d4ed8"/>
    </linearGradient>
    <linearGradient id="chk_hl" x1="1" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#fff" stop-opacity="0.3"/>
      <stop offset="100%" stop-color="#fff" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <circle cx="12" cy="12" r="10" fill="url(#chk_bg)"/>
  <circle cx="12" cy="12" r="10" fill="url(#chk_hl)"/>
  <path d="M7 12.5l3 3 7-7" stroke="#fff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
</svg>"""

WORM_SVG = """<svg class="w-full h-full" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="worm_body" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#405DE6"/>
      <stop offset="30%" stop-color="#833AB4"/>
      <stop offset="55%" stop-color="#E1306C"/>
      <stop offset="80%" stop-color="#FCAF45"/>
      <stop offset="100%" stop-color="#F77737"/>
    </linearGradient>
  </defs>
  <path d="M3 14 C3 9, 7 5, 11 7 C15 9, 17 15, 21 11" stroke="url(#worm_body)" stroke-width="3.5" stroke-linecap="round"/>
  <circle cx="21" cy="11" r="3.2" fill="url(#worm_body)"/>
  <circle cx="20" cy="10.3" r="0.65" fill="#fff"/>
  <circle cx="22" cy="10.3" r="0.65" fill="#fff"/>
  <circle cx="20" cy="10.3" r="0.3" fill="#333"/>
  <circle cx="22" cy="10.3" r="0.3" fill="#333"/>
  <path d="M19.5 12 C20 12.8, 21 12.8, 21.5 12" stroke="#fff" stroke-width="0.6" stroke-linecap="round"/>
</svg>"""

SC_SVG = """<svg class="w-full h-full" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="sc_grad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#FFD700"/>
      <stop offset="100%" stop-color="#FF8C00"/>
    </linearGradient>
    <linearGradient id="sc_grad2" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#FFD700"/>
      <stop offset="100%" stop-color="#FFA500"/>
    </linearGradient>
  </defs>
  <path d="M4 14.5a2 2 0 0 1 2-2h.5l1-5a3 3 0 0 1 3-2.5h1a3 3 0 0 1 3 3v.5" stroke="url(#sc_grad)" stroke-width="1.8" stroke-linecap="round"/>
  <path d="M12.5 8.5l-1 5.5a2 2 0 0 0 2 2H18a2 2 0 0 0 2-2v-.5a2 2 0 0 0-2-2h-.5l.5-2a2 2 0 0 0-2-2h-1a2 2 0 0 0-2 2v.5z" fill="url(#sc_grad2)" opacity="0.9"/>
  <rect x="4" y="13" width="1.5" height="4" rx="0.75" fill="url(#sc_grad)"/>
  <rect x="6.5" y="12" width="1.5" height="5" rx="0.75" fill="url(#sc_grad)"/>
  <rect x="9" y="11" width="1.5" height="6" rx="0.75" fill="url(#sc_grad)"/>
</svg>"""

BADGES = [
    {
        "name": "F11",
        "icon_svg": F11_SVG,
        "description": "Полноэкранный режим",
        "avatar_ring_gradient": "conic-gradient(from 0deg, #3b82f6, #8b5cf6, #6366f1, #3b82f6)",
        "avatar_ring_effect": "pulse",
    },
    {
        "name": "Проверено",
        "icon_svg": CHECK_SVG,
        "description": "Верифицированный пользователь",
        "avatar_ring_gradient": "conic-gradient(from 0deg, #0ea5e9, #2563eb, #0ea5e9)",
        "avatar_ring_effect": "spin",
    },
    {
        "name": "Червячок",
        "icon_svg": WORM_SVG,
        "description": "Преданный пользователь",
        "avatar_ring_gradient": "conic-gradient(from 0deg, #405DE6, #833AB4, #E1306C, #FCAF45, #F77737, #E1306C, #833AB4, #405DE6)",
        "avatar_ring_effect": "glow",
    },
    {
        "name": "Сын саундклауда",
        "icon_svg": SC_SVG,
        "description": "Любитель SoundCloud",
        "avatar_ring_gradient": "conic-gradient(from 0deg, #FFD700, #FFA500, #FFEC8B, #FFD700, #FFA500, #FFD700)",
        "avatar_ring_effect": "glow",
    },
]


async def seed():
    async with async_session_factory() as session:
        for b in BADGES:
            existing = await session.execute(select(Badge).where(Badge.name == b["name"]))
            badge = existing.scalar_one_or_none()
            if badge:
                badge.icon_svg = b["icon_svg"]
                badge.description = b["description"]
                badge.avatar_ring_gradient = b.get("avatar_ring_gradient")
                badge.avatar_ring_effect = b.get("avatar_ring_effect")
            else:
                session.add(Badge(**b))
        await session.commit()
        print("Badges seeded successfully")


if __name__ == "__main__":
    asyncio.run(seed())

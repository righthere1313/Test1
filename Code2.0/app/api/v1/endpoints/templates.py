from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from app.services.svg_layouts import layout_exists, list_layout_names, read_layout_design_spec, read_layout_svg, list_all_covers

router = APIRouter()


@router.get("/layouts", response_model=list[str])
async def list_layouts() -> List[str]:
    return list_layout_names()


@router.get("/layouts/design_spec", response_model=dict)
async def get_layout_design_spec(layout: str = Query(...)) -> Dict[str, str]:
    name = (layout or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="layout is required")
    if not layout_exists(name):
        raise HTTPException(status_code=404, detail="layout not found")
    spec = read_layout_design_spec(name) or ""
    return {"layout": name, "design_spec": spec}


@router.get("/layouts/svg", response_model=dict)
async def get_layout_svg(layout: str = Query(...), name: str = Query(...)) -> Dict[str, str]:
    layout_name = (layout or "").strip()
    svg_name = (name or "").strip()
    if not layout_name or not svg_name:
        raise HTTPException(status_code=400, detail="layout and name are required")
    if not layout_exists(layout_name):
        raise HTTPException(status_code=404, detail="layout not found")
    try:
        svg = read_layout_svg(layout_name, svg_name)
    except Exception:
        raise HTTPException(status_code=404, detail="svg not found")
    return {"layout": layout_name, "name": svg_name, "svg": svg}


@router.get("/covers", response_model=list[dict])
async def get_all_covers() -> List[Dict[str, str]]:
    return list_all_covers()

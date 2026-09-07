from __future__ import annotations

import json
from html import escape
from typing import Any


def render_html(report: dict[str, Any]) -> str:
    parts = []
    for index, item in enumerate(report["conflicts"]):
        values = "".join(
            "<section><h3>"
            + label.title()
            + "</h3><pre>"
            + escape(
                json.dumps(item[label], indent=2)
                if item["presence"][label]
                else "[DELETED / absent]"
            )
            + "</pre></section>"
            for label in ("base", "local", "remote")
        )
        parts.append(
            f'<article><h2>{escape(item["path"] or "/")}</h2><div class="triple">{values}</div><label>Resolution for {escape(item["path"] or "/")} <select data-index="{index}"><option value="">Unresolved</option><option value="local">Choose local</option><option value="remote">Choose remote</option></select></label></article>'
        )
    payload = (
        json.dumps(report, ensure_ascii=True)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )
    return (
        '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Sync conflict review</title><style>body{font:17px system-ui;background:#111e28;color:#eff6fa;padding:22px;max-width:1150px;margin:auto;line-height:1.6}article{border:1px solid #688699;border-radius:12px;padding:18px;margin:20px 0}.triple{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#203442;padding:14px}button,select{font:inherit;padding:10px}h2{overflow-wrap:anywhere}@media(max-width:650px){.triple{grid-template-columns:1fr}body{padding:12px}}output{display:block;margin:14px 0}</style><h1>Three-way conflict review</h1><p>Choose a side for each conflict. Download a replay plan, then use --replay with the same source snapshots. No source is edited; this is a local merge simulation. This report contains snapshot values: review before sharing.</p>'
        + "".join(parts)
        + '<button id="download">Download replay plan</button><output id="status" role="status"></output><script type="application/json" id="report">'
        + payload
        + "</script><script>"
        + r"""
const report=JSON.parse(document.getElementById('report').textContent);
for(const s of document.querySelectorAll('select'))s.value=report.choices[report.conflicts[Number(s.dataset.index)].path]||'';
document.getElementById('download').onclick=()=>{
const choices={};for(const s of document.querySelectorAll('select'))if(s.value)choices[report.conflicts[Number(s.dataset.index)].path]=s.value;
const plan={version:1,input_sha256:report.input_sha256,keyed_arrays:report.keyed_arrays,choices};
const url=URL.createObjectURL(new Blob([JSON.stringify(plan,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='sync-replay.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);document.getElementById('status').textContent=Object.keys(choices).length+' conflict choices exported. Replay validates source hashes.';
};
"""
        + "</script></html>"
    )

# """
# ╔══════════════════════════════════════════════════════════════╗
# ║    ⚡ ISSUES COMMAND NEXUS v3.0 — Premium White Dashboard    ║
# ║    Upload Excel / Google Sheet → Auto Next-Level Charts      ║
# ║    Run: python dashboard_app.py  → http://localhost:5050     ║
# ╚══════════════════════════════════════════════════════════════╝
# """
# import io, base64, threading, webbrowser, warnings
# warnings.filterwarnings('ignore')
# import pandas as pd
# from flask import Flask, render_template_string, request, jsonify

# app = Flask(__name__)

# # ── LOADERS ──────────────────────────────────
# def load_excel(b): return pd.read_excel(io.BytesIO(b))

# def load_gsheet(url):
#     import urllib.request
#     if '/edit' in url: url = url.split('/edit')[0]
#     if '/pub' in url:  csv_url = url.replace('/pub','/export')+'?format=csv'
#     elif 'spreadsheets/d/' in url:
#         sid = url.split('spreadsheets/d/')[1].split('/')[0]
#         csv_url = f'https://docs.google.com/spreadsheets/d/{sid}/export?format=csv'
#     else: raise ValueError("Invalid Google Sheets URL")
#     with urllib.request.urlopen(csv_url, timeout=12) as r:
#         return pd.read_csv(io.BytesIO(r.read()))

# # ── ANALYZER ─────────────────────────────────
# def analyze(df):
#     cat_cols  = [c for c in df.columns if df[c].dtype==object and 1<df[c].nunique()<80]
#     num_cols  = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
#     date_cols = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]

#     charts = []

#     # 1. Bar charts for categorical
#     for col in cat_cols[:10]:
#         vc = df[col].value_counts().head(15)
#         if len(vc)>=2:
#             charts.append({'id':f'bar_{col}','title':col,'type':'bar','col':col,
#                 'labels':vc.index.astype(str).tolist(),'values':vc.values.tolist()})

#     # 2. Donut for low-cardinality
#     done_donut=0
#     for col in cat_cols:
#         if 2<=df[col].nunique()<=8 and done_donut<4:
#             vc=df[col].value_counts()
#             charts.append({'id':f'donut_{col}','title':col,'type':'donut','col':col,
#                 'labels':vc.index.astype(str).tolist(),'values':vc.values.tolist()})
#             done_donut+=1

#     # 3. Line for date cols
#     for dcol in date_cols[:3]:
#         df2=df.copy(); df2[dcol]=pd.to_datetime(df2[dcol],errors='coerce')
#         monthly=df2.set_index(dcol).resample('ME').size()
#         if len(monthly)>=2:
#             charts.append({'id':f'line_{dcol}','title':dcol+' Trend','type':'line','col':dcol,
#                 'labels':monthly.index.strftime('%b %Y').tolist(),'values':monthly.values.tolist()})

#     # 4. Numeric histograms
#     for col in num_cols[:4]:
#         clean=df[col].dropna()
#         if len(clean)>5 and clean.max()<1e9:
#             _,edges=pd.cut(clean,bins=12,retbins=True)
#             counts=pd.cut(clean,bins=12).value_counts().sort_index()
#             charts.append({'id':f'hist_{col}','title':col+' Distribution','type':'area','col':col,
#                 'labels':[f'{e:.0f}' for e in edges[:-1]],'values':counts.values.tolist()})

#     # 5. Radar for multi-cat comparison (top 5 values of first cat vs count)
#     if len(cat_cols)>=2:
#         col=cat_cols[0]
#         vc=df[col].value_counts().head(8)
#         if len(vc)>=3:
#             charts.append({'id':f'radar_{col}','title':col+' Radar','type':'radar','col':col,
#                 'labels':vc.index.astype(str).tolist(),'values':vc.values.tolist()})

#     # Country map data (detect country column)
#     map_data = {}
#     for col in cat_cols:
#         if any(k in col.lower() for k in ['country','nation','location','region']):
#             vc=df[col].value_counts().head(30)
#             map_data={'col':col,'countries':vc.index.astype(str).tolist(),'counts':vc.values.tolist()}
#             break

#     # Stats
#     missing=(df.isnull().sum()/len(df)*100).round(1)
#     missing=missing[missing>0].sort_values(ascending=False).head(10)

#     num_stats={}
#     for col in num_cols:
#         s=df[col].dropna()
#         if len(s):
#             num_stats[col]={'count':int(len(s)),'mean':round(float(s.mean()),2),
#                 'min':round(float(s.min()),2),'max':round(float(s.max()),2),
#                 'std':round(float(s.std()),2),'median':round(float(s.median()),2),
#                 'q25':round(float(s.quantile(.25)),2),'q75':round(float(s.quantile(.75)),2)}

#     cat_stats={}
#     for col in cat_cols:
#         vc=df[col].value_counts()
#         cat_stats[col]={'unique':int(df[col].nunique()),
#             'top_val':str(vc.index[0]) if len(vc) else '—',
#             'top_count':int(vc.iloc[0]) if len(vc) else 0,
#             'missing_pct':round(df[col].isnull().mean()*100,1),
#             'breakdown':{'labels':vc.head(20).index.astype(str).tolist(),'values':vc.head(20).values.tolist()}}

#     date_stats={}
#     for col in date_cols:
#         s=pd.to_datetime(df[col],errors='coerce').dropna()
#         if len(s):
#             monthly=s.dt.to_period('M').value_counts().sort_index()
#             date_stats[col]={'count':int(len(s)),'min':str(s.min().date()),'max':str(s.max().date()),
#                 'missing_pct':round(df[col].isnull().mean()*100,1),
#                 'monthly_labels':[str(p) for p in monthly.index],'monthly_values':monthly.values.tolist()}

#     return {
#         'total_rows':len(df),'total_cols':len(df.columns),
#         'cat_cols':cat_cols,'num_cols':num_cols,'date_cols':date_cols,
#         'charts':charts,'map_data':map_data,
#         'table_cols':df.columns.tolist(),
#         'table_rows':df.head(300).fillna('—').astype(str).values.tolist(),
#         'missing':{'cols':missing.index.tolist(),'pcts':missing.values.tolist()},
#         'num_stats':num_stats,'cat_stats':cat_stats,'date_stats':date_stats,
#         'all_cols':df.columns.tolist()
#     }

# # ── HTML ─────────────────────────────────────
# HTML = r"""<!DOCTYPE html>
# <html lang="en">
# <head>
# <meta charset="UTF-8">
# <meta name="viewport" content="width=device-width,initial-scale=1.0">
# <title>⚡ Issues Command Nexus v3</title>
# <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
# <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2.2.0/dist/chartjs-plugin-datalabels.min.js"></script>
# <script src="https://cdn.jsdelivr.net/npm/chartjs-chart-geo@4.3.0/build/index.umd.min.js"></script>
# <style>
# @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Space+Grotesk:wght@400;500;600;700&display=swap');

# :root {
#   --bg: #f0f4ff;
#   --white: #ffffff;
#   --blue1: #1a56db;
#   --blue2: #3b82f6;
#   --blue3: #60a5fa;
#   --blue4: #bfdbfe;
#   --blue5: #eff6ff;
#   --navy: #1e3a8a;
#   --slate: #64748b;
#   --text: #0f172a;
#   --text2: #334155;
#   --text3: #64748b;
#   --border: rgba(59,130,246,0.15);
#   --shadow: 0 4px 24px rgba(30,58,138,0.10);
#   --shadow2: 0 12px 48px rgba(30,58,138,0.18);
#   --radius: 18px;
# }

# * { margin:0; padding:0; box-sizing:border-box; }
# html { scroll-behavior: smooth; }
# body {
#   font-family: 'Inter', sans-serif;
#   background: var(--bg);
#   color: var(--text);
#   min-height: 100vh;
#   overflow-x: hidden;
# }

# /* ── DECORATIVE BG ── */
# body::before {
#   content: '';
#   position: fixed;
#   top: -200px; right: -200px;
#   width: 600px; height: 600px;
#   background: radial-gradient(circle, rgba(59,130,246,0.12) 0%, transparent 70%);
#   pointer-events: none; z-index: 0;
# }
# body::after {
#   content: '';
#   position: fixed;
#   bottom: -200px; left: -200px;
#   width: 500px; height: 500px;
#   background: radial-gradient(circle, rgba(99,102,241,0.08) 0%, transparent 70%);
#   pointer-events: none; z-index: 0;
# }

# .page { position: relative; z-index: 1; max-width: 1600px; margin: 0 auto; padding: 24px 28px 60px; }

# /* ── HEADER ── */
# .hdr {
#   display: flex; align-items: center; justify-content: space-between;
#   padding: 20px 28px;
#   background: var(--white);
#   border-radius: var(--radius);
#   box-shadow: var(--shadow);
#   margin-bottom: 24px;
#   border: 1px solid var(--border);
#   animation: slideDown .6s ease both;
# }
# @keyframes slideDown { from{opacity:0;transform:translateY(-20px)} to{opacity:1;transform:translateY(0)} }
# .logo { display: flex; align-items: center; gap: 14px; }
# .logo-icon {
#   width: 44px; height: 44px;
#   background: linear-gradient(135deg, var(--blue1), var(--blue2));
#   border-radius: 12px;
#   display: flex; align-items: center; justify-content: center;
#   font-size: 20px;
#   box-shadow: 0 4px 14px rgba(26,86,219,.35);
# }
# .logo h1 {
#   font-family: 'Space Grotesk', sans-serif;
#   font-size: 20px; font-weight: 700;
#   color: var(--text);
#   letter-spacing: -0.5px;
# }
# .logo p { font-size: 12px; color: var(--text3); margin-top: 1px; }
# .hdr-right { display: flex; align-items: center; gap: 12px; }
# .live-pill {
#   display: flex; align-items: center; gap: 7px;
#   background: #ecfdf5; border: 1px solid #10b981;
#   border-radius: 20px; padding: 6px 14px;
#   font-size: 11px; font-weight: 600; color: #065f46;
#   letter-spacing: 0.5px;
# }
# .live-dot { width:7px;height:7px;border-radius:50%;background:#10b981;animation:livePulse 1.5s infinite; }
# @keyframes livePulse{0%,100%{box-shadow:0 0 0 0 rgba(16,185,129,.4)}50%{box-shadow:0 0 0 6px rgba(16,185,129,0)}}
# .date-pill {
#   background: var(--blue5); border: 1px solid var(--blue4);
#   border-radius: 10px; padding: 6px 14px;
#   font-size: 12px; font-weight: 500; color: var(--blue1);
# }

# /* ── UPLOAD ZONE ── */
# .upload-zone {
#   background: var(--white);
#   border: 2px dashed var(--blue3);
#   border-radius: var(--radius);
#   padding: 40px 24px;
#   text-align: center;
#   margin-bottom: 24px;
#   transition: all .3s;
#   animation: fadeUp .7s ease both;
#   box-shadow: var(--shadow);
# }
# @keyframes fadeUp { from{opacity:0;transform:translateY(24px)} to{opacity:1;transform:translateY(0)} }
# .upload-zone:hover, .upload-zone.drag { border-color: var(--blue1); background: var(--blue5); }
# .upload-zone h2 { font-family:'Space Grotesk',sans-serif; font-size:22px; font-weight:700; color:var(--text); margin-bottom:8px; }
# .upload-zone p { font-size:14px; color:var(--text3); margin-bottom:26px; }
# .up-icon { font-size: 52px; margin-bottom: 16px; display: block; filter: drop-shadow(0 4px 12px rgba(59,130,246,.3)); }
# .btn-row { display:flex; gap:12px; justify-content:center; flex-wrap:wrap; margin-bottom:16px; }
# .btn {
#   font-family:'Space Grotesk',sans-serif; font-size:13px; font-weight:600;
#   padding: 11px 24px; border-radius: 10px; border: none;
#   cursor: pointer; transition: all .22s; letter-spacing: 0.3px;
# }
# .btn-blue { background: var(--blue1); color: #fff; box-shadow: 0 4px 14px rgba(26,86,219,.35); }
# .btn-blue:hover { background: var(--navy); transform: translateY(-2px); box-shadow: 0 8px 20px rgba(26,86,219,.4); }
# .btn-outline { background: var(--white); color: var(--blue1); border: 1.5px solid var(--blue2); }
# .btn-outline:hover { background: var(--blue5); transform: translateY(-2px); }
# .btn-sm { padding: 7px 16px; font-size: 12px; }
# #fileInput { display:none; }
# .gurl {
#   width: 100%; max-width: 480px;
#   border: 1.5px solid var(--border);
#   border-radius: 10px; padding: 10px 16px;
#   font-family:'Inter',sans-serif; font-size: 13px;
#   color: var(--text); background: var(--white);
#   outline: none; transition: border-color .2s;
# }
# .gurl:focus { border-color: var(--blue2); box-shadow: 0 0 0 3px rgba(59,130,246,.15); }
# .gurl::placeholder { color: var(--text3); }
# .warn-note { font-size:11px; color:#b45309; margin-top:10px; }

# /* ── LOADER ── */
# #loader {
#   display:none; position:fixed; inset:0;
#   background: rgba(255,255,255,.9);
#   backdrop-filter: blur(8px);
#   z-index: 2000; align-items:center; justify-content:center; flex-direction:column; gap:20px;
# }
# .spinner-ring {
#   width:60px; height:60px;
#   border: 4px solid var(--blue4);
#   border-top-color: var(--blue1);
#   border-radius: 50%; animation: spin 1s linear infinite;
# }
# @keyframes spin{to{transform:rotate(360deg)}}
# #loader p { font-family:'Space Grotesk',sans-serif; font-size:14px; font-weight:600; color:var(--blue1); letter-spacing:.5px; }

# /* ── DASHBOARD ── */
# #dash { display:none; }

# /* KPI CARDS */
# .kpi-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr)); gap:16px; margin-bottom:24px; }
# .kpi {
#   background: var(--white);
#   border-radius: var(--radius);
#   padding: 20px 22px;
#   cursor: pointer;
#   transition: transform .25s, box-shadow .25s;
#   border: 1px solid var(--border);
#   box-shadow: var(--shadow);
#   position: relative; overflow: hidden;
#   animation: fadeUp .5s ease both;
# }
# .kpi::after {
#   content:'';position:absolute;top:0;right:0;width:80px;height:80px;
#   background: radial-gradient(circle at 80% 20%, var(--kpi-color, rgba(59,130,246,.12)), transparent 70%);
#   pointer-events:none;
# }
# .kpi:hover { transform:translateY(-5px); box-shadow:var(--shadow2); }
# .kpi-top { display:flex; align-items:flex-start; justify-content:space-between; margin-bottom:12px; }
# .kpi-icon {
#   width:42px; height:42px; border-radius:12px;
#   background: var(--kpi-bg, var(--blue5));
#   display:flex; align-items:center; justify-content:center;
#   font-size:20px;
# }
# .kpi-badge {
#   font-size:10px; font-weight:600; letter-spacing:.5px;
#   padding:3px 8px; border-radius:6px;
#   background: var(--kpi-badge-bg, var(--blue5));
#   color: var(--kpi-badge-color, var(--blue1));
# }
# .kpi-val {
#   font-family:'Space Grotesk',sans-serif;
#   font-size:clamp(28px,4vw,42px); font-weight:800;
#   color: var(--kpi-color, var(--blue1));
#   line-height:1; letter-spacing:-1px;
# }
# .kpi-label { font-size:12px; font-weight:500; color:var(--text3); margin-top:4px; }
# .kpi-hint { font-size:10px; color:var(--blue3); margin-top:6px; opacity:0; transition:opacity .2s; }
# .kpi:hover .kpi-hint { opacity:1; }
# .kpi-trend { font-size:11px; color:#10b981; font-weight:600; margin-top:4px; }

# /* SECTION TITLE */
# .section-title {
#   font-family:'Space Grotesk',sans-serif;
#   font-size:16px; font-weight:700; color:var(--text);
#   display:flex; align-items:center; gap:10px; margin-bottom:16px;
# }
# .section-title::before {
#   content:''; width:4px; height:20px;
#   background:linear-gradient(to bottom, var(--blue1), var(--blue3));
#   border-radius:2px;
# }

# /* CHART CARDS */
# .chart-card {
#   background: var(--white);
#   border-radius: var(--radius);
#   padding: 22px;
#   border: 1px solid var(--border);
#   box-shadow: var(--shadow);
#   transition: box-shadow .25s;
#   position: relative; overflow: hidden;
#   cursor: pointer;
# }
# .chart-card:hover { box-shadow: var(--shadow2); }
# .chart-card::before {
#   content:''; position:absolute; top:0;left:0;right:0;height:3px;
#   background: var(--card-accent, linear-gradient(90deg,var(--blue1),var(--blue3)));
# }
# .card-hdr { display:flex; align-items:center; justify-content:space-between; margin-bottom:18px; }
# .card-title { font-family:'Space Grotesk',sans-serif; font-size:13px; font-weight:700; color:var(--text); }
# .card-badge {
#   font-size:10px; font-weight:600; padding:3px 9px;
#   border-radius:6px; background:var(--blue5); color:var(--blue1);
#   border: 1px solid var(--blue4);
# }
# canvas.ch { max-height:280px; }

# /* GRIDS */
# .g1{display:grid;grid-template-columns:1fr;gap:18px;margin-bottom:20px}
# .g2{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-bottom:20px}
# .g3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:18px;margin-bottom:20px}
# .g12{display:grid;grid-template-columns:1.8fr 1fr;gap:18px;margin-bottom:20px}
# .g21{display:grid;grid-template-columns:1fr 1.8fr;gap:18px;margin-bottom:20px}

# /* MAP CARD */
# .map-card {
#   background: var(--white);
#   border-radius: var(--radius);
#   padding: 22px;
#   border: 1px solid var(--border);
#   box-shadow: var(--shadow);
#   min-height: 380px;
#   position: relative; overflow: hidden;
# }
# .map-card::before {
#   content:'';position:absolute;top:0;left:0;right:0;height:3px;
#   background: linear-gradient(90deg,#10b981,#3b82f6);
# }
# #map-container { position:relative; }
# #world-map { width:100%; height:300px; border-radius:12px; }

# /* TABS */
# .tab-bar { display:flex; gap:4px; margin-bottom:20px; background:var(--blue5); padding:4px; border-radius:12px; width:fit-content; }
# .tab {
#   font-family:'Space Grotesk',sans-serif; font-size:12px; font-weight:600;
#   padding:8px 18px; border-radius:9px; border:none;
#   cursor:pointer; transition:all .2s; color:var(--text3); background:transparent;
# }
# .tab.active { background:var(--white); color:var(--blue1); box-shadow:0 2px 8px rgba(30,58,138,.12); }
# .tab:hover:not(.active) { color:var(--blue1); background:rgba(255,255,255,.6); }
# .tc { display:none; } .tc.active { display:block; }

# /* COLUMN PILLS */
# .pills-card {
#   background:var(--white); border-radius:var(--radius);
#   padding:18px 20px; border:1px solid var(--border);
#   box-shadow:var(--shadow); margin-bottom:20px;
# }
# .pills-wrap { display:flex; flex-wrap:wrap; gap:8px; margin-top:12px; }
# .pill {
#   font-size:12px; font-weight:500; padding:5px 14px;
#   border-radius:20px; cursor:pointer; transition:all .2s;
#   border:1.5px solid; white-space:nowrap;
# }
# .pill-cat { border-color:#3b82f6; color:#1d4ed8; background:#eff6ff; }
# .pill-cat:hover { background:#1d4ed8; color:#fff; box-shadow:0 4px 12px rgba(29,78,216,.3); }
# .pill-num { border-color:#10b981; color:#065f46; background:#ecfdf5; }
# .pill-num:hover { background:#065f46; color:#fff; box-shadow:0 4px 12px rgba(6,95,70,.3); }
# .pill-date { border-color:#8b5cf6; color:#5b21b6; background:#f5f3ff; }
# .pill-date:hover { background:#5b21b6; color:#fff; box-shadow:0 4px 12px rgba(91,33,182,.3); }

# /* TABLE */
# .tbl-wrap { overflow:auto; max-height:400px; border-radius:12px; border:1px solid var(--border); }
# .tbl-wrap::-webkit-scrollbar { width:5px;height:5px; }
# .tbl-wrap::-webkit-scrollbar-thumb { background:var(--blue4); border-radius:3px; }
# table { width:100%; border-collapse:collapse; font-size:12.5px; }
# thead { position:sticky; top:0; z-index:10; }
# th { background:var(--blue1); color:#fff; padding:10px 14px; font-weight:600; text-align:left; white-space:nowrap; font-size:11px; letter-spacing:.3px; }
# th:first-child { border-radius:0; } 
# td { padding:9px 14px; color:var(--text2); border-bottom:1px solid #f1f5f9; white-space:nowrap; max-width:180px; overflow:hidden; text-overflow:ellipsis; }
# tr:hover td { background:#f8faff; }
# tr:nth-child(even) td { background:#f8faff; }
# tr:nth-child(even):hover td { background:#eef4ff; }

# /* MODAL */
# #modal-overlay {
#   display:none; position:fixed; inset:0;
#   background:rgba(15,23,42,.5); backdrop-filter:blur(8px);
#   z-index:3000; align-items:center; justify-content:center; padding:20px;
# }
# #modal-overlay.open { display:flex; }
# #modal-box {
#   background:var(--white); border-radius:24px;
#   width:100%; max-width:860px; max-height:90vh; overflow-y:auto;
#   box-shadow:0 24px 80px rgba(15,23,42,.25);
#   animation:modalPop .3s cubic-bezier(.34,1.56,.64,1) both;
#   border:1px solid var(--border);
# }
# @keyframes modalPop { from{opacity:0;transform:scale(.9) translateY(20px)} to{opacity:1;transform:scale(1) translateY(0)} }
# #modal-box::-webkit-scrollbar { width:5px; }
# #modal-box::-webkit-scrollbar-thumb { background:var(--blue4); border-radius:3px; }
# .modal-hdr {
#   display:flex; align-items:center; justify-content:space-between;
#   padding:20px 24px 16px; border-bottom:1px solid #f1f5f9;
#   position:sticky; top:0; background:var(--white); z-index:5; border-radius:24px 24px 0 0;
# }
# .modal-title { font-family:'Space Grotesk',sans-serif; font-size:16px; font-weight:700; color:var(--text); }
# .modal-close {
#   width:32px;height:32px; border-radius:8px;
#   background:#fee2e2; border:none; color:#dc2626;
#   cursor:pointer; font-size:16px; display:flex; align-items:center; justify-content:center;
#   transition:all .2s;
# }
# .modal-close:hover { background:#dc2626; color:#fff; }
# .modal-body { padding:22px 24px; }
# .stat-row { display:grid; grid-template-columns:repeat(auto-fit,minmax(110px,1fr)); gap:12px; margin-bottom:20px; }
# .stat-box {
#   background:var(--blue5); border:1px solid var(--blue4);
#   border-radius:12px; padding:14px; text-align:center;
# }
# .stat-val { font-family:'Space Grotesk',sans-serif; font-size:20px; font-weight:800; color:var(--blue1); }
# .stat-lbl { font-size:10px; font-weight:500; color:var(--text3); margin-top:3px; text-transform:uppercase; letter-spacing:.5px; }
# .detail-tbl { width:100%; border-collapse:collapse; font-size:13px; }
# .detail-tbl th { background:#f8faff; color:var(--text3); padding:9px 12px; font-size:10px; text-transform:uppercase; letter-spacing:.5px; font-weight:600; border-bottom:1px solid #e2e8f0; text-align:left; }
# .detail-tbl td { padding:10px 12px; color:var(--text2); border-bottom:1px solid #f1f5f9; }
# .detail-tbl tr:hover td { background:#f8faff; }
# .dbar-bg { width:100%; background:#e2e8f0; border-radius:4px; height:6px; overflow:hidden; }
# .dbar { height:100%; border-radius:4px; background:linear-gradient(90deg,var(--blue1),var(--blue3)); transition:width 1.2s ease; }

# /* MISSING BARS */
# .mbar-item { margin-bottom:14px; }
# .mbar-top { display:flex; justify-content:space-between; font-size:12px; margin-bottom:4px; color:var(--text2); }
# .mbar-pct { font-weight:700; color:#dc2626; }
# .mbar-bg { width:100%; background:#fee2e2; border-radius:4px; height:8px; overflow:hidden; }
# .mbar-fill { height:100%; border-radius:4px; background:linear-gradient(90deg,#dc2626,#f87171); transition:width 1.5s ease; }

# /* ── MISC UTIL ── */
# .hint-bar {
#   text-align:center; padding:8px; margin-bottom:14px;
#   font-size:11px; font-weight:600; color:var(--blue1);
#   background:var(--blue5); border-radius:10px; letter-spacing:.5px;
#   border:1px solid var(--blue4);
# }

# /* SCROLLBAR MAIN */
# ::-webkit-scrollbar { width:6px; }
# ::-webkit-scrollbar-thumb { background:var(--blue4); border-radius:3px; }

# /* RESPONSIVE */
# @media(max-width:900px){.g2,.g3,.g12,.g21{grid-template-columns:1fr}.kpi-grid{grid-template-columns:repeat(2,1fr)}}
# </style>
# </head>
# <body>

# <!-- LOADER -->
# <div id="loader"><div class="spinner-ring"></div><p id="ltxt">ANALYZING DATA...</p></div>

# <!-- MODAL -->
# <div id="modal-overlay" onclick="if(event.target===this)closeModal()">
#   <div id="modal-box">
#     <div class="modal-hdr">
#       <div class="modal-title" id="modal-title">Detail</div>
#       <button class="modal-close" onclick="closeModal()">✕</button>
#     </div>
#     <div class="modal-body" id="modal-body"></div>
#   </div>
# </div>

# <div class="page">

#   <!-- HEADER -->
#   <div class="hdr">
#     <div class="logo">
#       <div class="logo-icon">⚡</div>
#       <div>
#         <h1>Issues Command Nexus</h1>
#         <p>Next-Level Data Intelligence Dashboard v3.0</p>
#       </div>
#     </div>
#     <div class="hdr-right">
#       <div class="date-pill" id="datepill">Loading...</div>
#       <div class="live-pill"><div class="live-dot"></div>LIVE</div>
#     </div>
#   </div>

#   <!-- UPLOAD -->
#   <div class="upload-zone" id="dropZone">
#     <span class="up-icon">📊</span>
#     <h2>Connect Your Data Source</h2>
#     <p>Drag & drop Excel / CSV file — or paste your Google Sheets URL below</p>
#     <div class="btn-row">
#       <button class="btn btn-blue" onclick="document.getElementById('fileInput').click()">📂 Upload Excel / CSV</button>
#       <input type="file" id="fileInput" accept=".xlsx,.xls,.csv">
#     </div>
#     <div class="btn-row">
#       <input class="gurl" id="gurl" type="url" placeholder="https://docs.google.com/spreadsheets/d/...">
#       <button class="btn btn-outline" onclick="loadGSheet()">🔗 Load Google Sheet</button>
#     </div>
#     <p class="warn-note">⚠️ Google Sheet must be: Share → Anyone with link → Viewer</p>
#   </div>

#   <!-- DASHBOARD (hidden until data) -->
#   <div id="dash">
#     <div class="hint-bar">👆 KPI cards aur charts pe click karo — full detail dekhne ke liye</div>

#     <!-- KPI CARDS -->
#     <div class="kpi-grid" id="kpi-grid"></div>

#     <!-- WORLD MAP + TOP COUNTRIES -->
#     <div id="map-section" style="display:none" class="g12">
#       <div class="map-card">
#         <div class="card-hdr">
#           <div class="card-title">🌍 Country Distribution Map</div>
#           <div class="card-badge" id="map-badge">GLOBAL</div>
#         </div>
#         <canvas id="world-map-canvas" class="ch"></canvas>
#         <div id="map-legend" style="display:flex;flex-wrap:wrap;gap:8px;margin-top:12px;font-size:11px;color:var(--text3)"></div>
#       </div>
#       <div class="chart-card">
#         <div class="card-hdr">
#           <div class="card-title">🏆 Top Countries</div>
#           <div class="card-badge" id="country-badge">RANKING</div>
#         </div>
#         <canvas id="country-bar" class="ch"></canvas>
#       </div>
#     </div>

#     <!-- CHARTS SECTION -->
#     <div class="section-title">📊 Smart Analytics</div>
#     <div id="charts-container"></div>

#     <!-- COLUMN EXPLORER -->
#     <div class="pills-card">
#       <div class="section-title" style="margin-bottom:0">🔍 Column Explorer — Click to Inspect</div>
#       <div class="pills-wrap" id="cpills"></div>
#     </div>

#     <!-- TABS -->
#     <div class="tab-bar">
#       <button class="tab active" onclick="showTab('table',this)">📋 Data Table</button>
#       <button class="tab" onclick="showTab('quality',this)">🔬 Data Quality</button>
#     </div>

#     <div class="tc active" id="tc-table">
#       <div class="chart-card" style="cursor:default">
#         <div class="card-hdr">
#           <div class="card-title">Raw Data</div>
#           <div class="card-badge" id="rbadge">RECORDS</div>
#         </div>
#         <div class="tbl-wrap"><table id="dtbl"></table></div>
#       </div>
#     </div>

#     <div class="tc" id="tc-quality">
#       <div class="g2">
#         <div class="chart-card" style="cursor:default">
#           <div class="card-hdr"><div class="card-title">⚠️ Missing Data Analysis</div></div>
#           <div id="mchrt"></div>
#         </div>
#         <div class="chart-card" style="cursor:default">
#           <div class="card-hdr"><div class="card-title">🗂️ Column Type Summary</div></div>
#           <div id="csum"></div>
#         </div>
#       </div>
#     </div>
#   </div>
# </div>

# <script>
# // ── DATE ──
# document.getElementById('datepill').textContent = new Date().toLocaleDateString('en-IN',{day:'2-digit',month:'short',year:'numeric'});

# // ── DRAG DROP ──
# const dz=document.getElementById('dropZone');
# dz.addEventListener('dragover',e=>{e.preventDefault();dz.classList.add('drag')});
# dz.addEventListener('dragleave',()=>dz.classList.remove('drag'));
# dz.addEventListener('drop',e=>{e.preventDefault();dz.classList.remove('drag');if(e.dataTransfer.files[0])processFile(e.dataTransfer.files[0])});
# document.getElementById('fileInput').addEventListener('change',e=>{if(e.target.files[0])processFile(e.target.files[0])});

# function showLoader(t){document.getElementById('ltxt').textContent=t;document.getElementById('loader').style.display='flex'}
# function hideLoader(){document.getElementById('loader').style.display='none'}
# function showTab(n,btn){
#   document.querySelectorAll('.tc').forEach(t=>t.classList.remove('active'));
#   document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
#   document.getElementById('tc-'+n).classList.add('active');
#   btn.classList.add('active');
# }

# function processFile(f){
#   showLoader('PARSING FILE...');
#   const fr=new FileReader();
#   fr.onload=e=>{
#     const b64=btoa(new Uint8Array(e.target.result).reduce((d,b)=>d+String.fromCharCode(b),''));
#     fetch('/analyze',{method:'POST',headers:{'Content-Type':'application/json'},
#       body:JSON.stringify({type:'file',data:b64,name:f.name})})
#     .then(r=>r.json()).then(renderDash).catch(err=>{hideLoader();alert('Error: '+err)});
#   };fr.readAsArrayBuffer(f);
# }

# function loadGSheet(){
#   const url=document.getElementById('gurl').value.trim();
#   if(!url){alert('Google Sheet URL daalo');return}
#   showLoader('FETCHING SHEET...');
#   fetch('/analyze',{method:'POST',headers:{'Content-Type':'application/json'},
#     body:JSON.stringify({type:'gsheet',url})})
#   .then(r=>r.json()).then(renderDash).catch(err=>{hideLoader();alert('Error: '+err)});
# }

# // ── GLOBAL DATA ──
# let GDATA=null, chartInsts=[], mapInst=null, mChartInst=null;

# // ── CHART COLORS ──
# const COLORS=[
#   '#1a56db','#3b82f6','#60a5fa','#1e3a8a','#0ea5e9','#0284c7','#2563eb',
#   '#0891b2','#0369a1','#4f46e5','#6366f1','#8b5cf6','#10b981','#059669',
#   '#0d9488','#14b8a6','#6d28d9','#7c3aed','#9333ea','#a855f7'
# ];
# const LIGHT_COLORS=COLORS.map(c=>c+'33');
# const BC={
#   responsive:true,maintainAspectRatio:true,
#   plugins:{
#     legend:{labels:{color:'#334155',font:{family:'Inter',size:12},padding:14}},
#     tooltip:{
#       backgroundColor:'#fff',borderColor:'#e2e8f0',borderWidth:1,
#       titleColor:'#0f172a',bodyColor:'#334155',padding:12,
#       titleFont:{family:'Space Grotesk',size:13,weight:'700'},
#       bodyFont:{family:'Inter',size:12},
#       shadowOffsetX:0,shadowOffsetY:4,shadowBlur:12,shadowColor:'rgba(0,0,0,.1)',
#       displayColors:true
#     }
#   }
# };

# function animCount(el,target){
#   const dur=1200,st=performance.now();
#   (function s(now){const p=Math.min((now-st)/dur,1),e=1-Math.pow(1-p,4);
#     el.textContent=Math.round(e*target).toLocaleString();if(p<1)requestAnimationFrame(s)})(performance.now());
# }

# // ── KPI CONFIG ──
# const KPI_CONFIG=[
#   {key:'total_rows',label:'Total Records',icon:'📁',bg:'#eff6ff',color:'#1d4ed8',badge:'TOTAL',badgeBg:'#dbeafe',badgeColor:'#1d4ed8',kpiColor:'rgba(59,130,246,.1)'},
#   {key:'cat_len',label:'Text Columns',icon:'🔤',bg:'#ecfdf5',color:'#065f46',badge:'TEXT',badgeBg:'#d1fae5',badgeColor:'#065f46',kpiColor:'rgba(16,185,129,.1)'},
#   {key:'num_len',label:'Numeric Cols',icon:'🔢',bg:'#faf5ff',color:'#5b21b6',badge:'NUM',badgeBg:'#ede9fe',badgeColor:'#5b21b6',kpiColor:'rgba(139,92,246,.1)'},
#   {key:'date_len',label:'Date Columns',icon:'📅',bg:'#fff7ed',color:'#9a3412',badge:'DATE',badgeBg:'#fed7aa',badgeColor:'#9a3412',kpiColor:'rgba(249,115,22,.1)'},
#   {key:'charts_len',label:'Auto Charts',icon:'📊',bg:'#fdf2f8',color:'#831843',badge:'CHARTS',badgeBg:'#fce7f3',badgeColor:'#831843',kpiColor:'rgba(236,72,153,.1)'},
#   {key:'missing_len',label:'Missing Cols',icon:'⚠️',bg:'#fef2f2',color:'#991b1b',badge:'GAP',badgeBg:'#fee2e2',badgeColor:'#991b1b',kpiColor:'rgba(239,68,68,.1)'},
# ];

# // ── MODAL ──
# function openModal(type,key){
#   if(!GDATA)return;
#   if(mChartInst){mChartInst.destroy();mChartInst=null}
#   const body=document.getElementById('modal-body'),title=document.getElementById('modal-title');
#   body.innerHTML='';
#   if(type==='summary')   renderSummaryModal(title,body);
#   else if(type==='cat')  renderCatModal(key,title,body);
#   else if(type==='num')  renderNumModal(key,title,body);
#   else if(type==='date') renderDateModal(key,title,body);
#   document.getElementById('modal-overlay').classList.add('open');
# }
# function closeModal(){
#   document.getElementById('modal-overlay').classList.remove('open');
#   if(mChartInst){mChartInst.destroy();mChartInst=null}
# }
# document.addEventListener('keydown',e=>{if(e.key==='Escape')closeModal()});

# function sbox(val,lbl,color='var(--blue1)'){
#   return `<div class="stat-box"><div class="stat-val" style="color:${color}">${val}</div><div class="stat-lbl">${lbl}</div></div>`;
# }

# function renderSummaryModal(title,body){
#   title.textContent='📊 Dataset Overview';
#   body.innerHTML=`<div class="stat-row">
#     ${sbox(GDATA.total_rows.toLocaleString(),'Total Rows')}
#     ${sbox(GDATA.total_cols,'Columns')}
#     ${sbox(GDATA.cat_cols.length,'Text Cols','#10b981')}
#     ${sbox(GDATA.num_cols.length,'Numeric','#8b5cf6')}
#     ${sbox(GDATA.date_cols.length,'Date Cols','#f59e0b')}
#     ${sbox(GDATA.missing.cols.length,'Missing','#dc2626')}
#   </div>
#   <div style="font-size:13px;font-weight:700;color:var(--text);margin-bottom:12px">All Columns</div>
#   <div style="display:flex;flex-wrap:wrap;gap:8px">
#     ${GDATA.all_cols.map(c=>{
#       let cls='pill-cat',type='TEXT';
#       if(GDATA.num_cols.includes(c)){cls='pill-num';type='NUM'}
#       else if(GDATA.date_cols.includes(c)){cls='pill-date';type='DATE'}
#       return `<span class="pill ${cls}" style="cursor:pointer" onclick="closeModal();setTimeout(()=>{${GDATA.num_cols.includes(c)?`openModal('num','${c}')`:(GDATA.date_cols.includes(c)?`openModal('date','${c}')`:`openModal('cat','${c}')`)}},120)">${c}<span style="opacity:.5;margin-left:4px;font-size:9px">${type}</span></span>`;
#     }).join('')}
#   </div>`;
# }

# function renderCatModal(key,title,body){
#   const s=GDATA.cat_stats[key]; if(!s)return;
#   title.textContent='🔤 '+key;
#   const maxV=Math.max(...s.breakdown.values);
#   body.innerHTML=`<div class="stat-row">
#     ${sbox(s.unique,'Unique Values','#1d4ed8')}
#     ${sbox(s.top_val,'Top Value','#059669')}
#     ${sbox(s.top_count,'Top Count','#7c3aed')}
#     ${sbox(s.missing_pct+'%','Missing',s.missing_pct>0?'#dc2626':'#10b981')}
#   </div>
#   <table class="detail-tbl">
#     <thead><tr><th>#</th><th>Value</th><th>Count</th><th>Share</th><th>Distribution</th></tr></thead>
#     <tbody>${s.breakdown.labels.map((lbl,i)=>{
#       const v=s.breakdown.values[i];
#       const pct=((v/GDATA.total_rows)*100).toFixed(1);
#       const bpct=Math.round((v/maxV)*100);
#       return `<tr>
#         <td style="color:var(--text3);font-size:11px">${i+1}</td>
#         <td style="font-weight:600">${lbl}</td>
#         <td style="font-weight:700;color:var(--blue1)">${v.toLocaleString()}</td>
#         <td style="color:#10b981;font-weight:600">${pct}%</td>
#         <td style="min-width:120px"><div style="display:flex;align-items:center;gap:6px">
#           <div class="dbar-bg" style="flex:1"><div class="dbar" style="width:0%" data-w="${bpct}%"></div></div>
#           <span style="font-size:10px;color:var(--text3);width:30px">${bpct}%</span>
#         </div></td>
#       </tr>`;}).join('')}
#     </tbody>
#   </table>
#   <div style="margin-top:22px;height:220px;position:relative"><canvas id="mchart"></canvas></div>`;
#   setTimeout(()=>{
#     document.querySelectorAll('.dbar').forEach(b=>b.style.width=b.dataset.w);
#     mChartInst=new Chart(document.getElementById('mchart'),{
#       type:'bar',
#       data:{labels:s.breakdown.labels,datasets:[{data:s.breakdown.values,
#         backgroundColor:COLORS.slice(0,s.breakdown.labels.length).map(c=>c+'cc'),
#         borderColor:COLORS.slice(0,s.breakdown.labels.length),
#         borderWidth:2,borderRadius:8,borderSkipped:false}]},
#       options:{...BC,indexAxis:s.breakdown.labels.length>7?'y':'x',maintainAspectRatio:false,
#         plugins:{...BC.plugins,legend:{display:false}},
#         animation:{delay:ctx=>ctx.dataIndex*40,duration:700,easing:'easeOutCubic'},
#         scales:{x:{grid:{color:'#f1f5f9'},ticks:{font:{size:11}}},
#                 y:{grid:{color:'#f1f5f9'},beginAtZero:true,ticks:{font:{size:11}}}}}
#     });
#   },120);
# }

# function renderNumModal(key,title,body){
#   const s=GDATA.num_stats[key]; if(!s)return;
#   title.textContent='🔢 '+key;
#   body.innerHTML=`<div class="stat-row">
#     ${sbox(s.count.toLocaleString(),'Count')}
#     ${sbox(s.mean.toLocaleString(),'Average','#7c3aed')}
#     ${sbox(s.median.toLocaleString(),'Median','#059669')}
#     ${sbox(s.min.toLocaleString(),'Min','#0284c7')}
#     ${sbox(s.max.toLocaleString(),'Max','#dc2626')}
#     ${sbox(s.std.toLocaleString(),'Std Dev','#64748b')}
#     ${sbox(s.q25.toLocaleString(),'Q1 (25%)','#0d9488')}
#     ${sbox(s.q75.toLocaleString(),'Q3 (75%)','#9333ea')}
#   </div>
#   <div style="margin-top:16px;height:200px;position:relative"><canvas id="mchart"></canvas></div>`;
#   setTimeout(()=>{
#     const hch=GDATA.charts.find(c=>c.id===`hist_${key}` || c.id===`area_${key}`);
#     if(hch){
#       mChartInst=new Chart(document.getElementById('mchart'),{
#         type:'bar',
#         data:{labels:hch.labels,datasets:[{label:'Frequency',data:hch.values,
#           backgroundColor:'#3b82f644',borderColor:'#1a56db',borderWidth:2,borderRadius:6,borderSkipped:false}]},
#         options:{...BC,maintainAspectRatio:false,plugins:{...BC.plugins,legend:{display:false}},
#           animation:{duration:800},
#           scales:{x:{grid:{color:'#f1f5f9'},title:{display:true,text:key,color:'#64748b',font:{size:11}}},
#                   y:{grid:{color:'#f1f5f9'},beginAtZero:true,title:{display:true,text:'Count',color:'#64748b',font:{size:11}}}}}
#       });
#     }
#   },120);
# }

# function renderDateModal(key,title,body){
#   const s=GDATA.date_stats[key]; if(!s)return;
#   title.textContent='📅 '+key;
#   body.innerHTML=`<div class="stat-row">
#     ${sbox(s.count.toLocaleString(),'Valid Dates','#7c3aed')}
#     ${sbox(s.min,'Earliest','#059669')}
#     ${sbox(s.max,'Latest','#dc2626')}
#     ${sbox(s.missing_pct+'%','Missing',s.missing_pct>0?'#dc2626':'#10b981')}
#   </div>
#   <div style="margin-top:16px;height:200px;position:relative"><canvas id="mchart"></canvas></div>`;
#   setTimeout(()=>{
#     if(s.monthly_labels.length>=2){
#       mChartInst=new Chart(document.getElementById('mchart'),{
#         type:'line',
#         data:{labels:s.monthly_labels,datasets:[{label:'Issues/Month',data:s.monthly_values,
#           borderColor:'#7c3aed',backgroundColor:'#7c3aed22',borderWidth:2.5,tension:.4,fill:true,
#           pointBackgroundColor:'#7c3aed',pointBorderColor:'#fff',pointBorderWidth:2,pointRadius:5}]},
#         options:{...BC,maintainAspectRatio:false,animation:{duration:1000},
#           scales:{x:{grid:{color:'#f1f5f9'},ticks:{font:{size:10}}},
#                   y:{grid:{color:'#f1f5f9'},beginAtZero:true}}}
#       });
#     }
#   },120);
# }

# // ── RENDER MAIN DASH ──
# function renderDash(data){
#   hideLoader();
#   if(data.error){alert('Error: '+data.error);return}
#   GDATA=data;

#   // Shrink upload
#   const uz=document.getElementById('dropZone');
#   uz.innerHTML=`<div style="display:flex;align-items:center;justify-content:space-between">
#     <span style="font-size:13px;color:var(--text3);font-weight:500">✅ Data loaded — drag a new file here to reload</span>
#     <button class="btn btn-outline btn-sm" onclick="document.getElementById('fileInput').click()">📂 Change File</button>
#   </div>`;
#   uz.style.cssText='padding:14px 20px;margin-bottom:20px;border-style:solid;border-radius:12px;background:var(--white)';

#   document.getElementById('dash').style.display='block';

#   // ── KPI CARDS ──
#   const kgrid=document.getElementById('kpi-grid'); kgrid.innerHTML='';
#   const kpiVals={
#     total_rows:data.total_rows, cat_len:data.cat_cols.length,
#     num_len:data.num_cols.length, date_len:data.date_cols.length,
#     charts_len:data.charts.length, missing_len:data.missing.cols.length
#   };

#   KPI_CONFIG.forEach((k,i)=>{
#     const val=kpiVals[k.key];
#     if(k.key!=='total_rows' && val===0) return; // hide zero cards
#     const div=document.createElement('div');
#     div.className='kpi';
#     div.style.cssText=`animation-delay:${i*.06}s;--kpi-color:${k.kpiColor};--kpi-bg:${k.bg};--kpi-badge-bg:${k.badgeBg};--kpi-badge-color:${k.badgeColor}`;
#     div.innerHTML=`
#       <div class="kpi-top">
#         <div class="kpi-icon" style="background:${k.bg}">${k.icon}</div>
#         <div class="kpi-badge" style="background:${k.badgeBg};color:${k.badgeColor}">${k.badge}</div>
#       </div>
#       <div class="kpi-val" style="color:${k.color}" id="kv_${k.key}">0</div>
#       <div class="kpi-label">${k.label}</div>
#       <div class="kpi-hint">Click for details →</div>`;
#     div.addEventListener('click',()=>openModal('summary',null));
#     kgrid.appendChild(div);
#     setTimeout(()=>animCount(document.getElementById('kv_'+k.key),val),i*60);
#   });

#   // ── WORLD MAP ──
#   if(data.map_data && data.map_data.countries && data.map_data.countries.length>0){
#     document.getElementById('map-section').style.display='grid';
#     document.getElementById('map-badge').textContent=data.map_data.col.toUpperCase();
#     document.getElementById('country-badge').textContent=data.map_data.countries.length+' COUNTRIES';
#     renderWorldMap(data.map_data);
#     renderCountryBar(data.map_data);
#   }

#   // ── CHARTS ──
#   chartInsts.forEach(c=>c.destroy()); chartInsts=[];
#   const cc=document.getElementById('charts-container'); cc.innerHTML='';

#   const charts=data.charts;
#   let i=0;
#   while(i<charts.length){
#     const rem=charts.length-i;
#     let cnt=rem===1?1:rem===2?2:3;
#     // Large charts (bar with many labels) get more space
#     if(rem>=2 && charts[i].labels && charts[i].labels.length>8) cnt=Math.min(2,rem);
#     const gridClass=['g1','g2','g3'][cnt-1];
#     const row=document.createElement('div'); row.className=gridClass;
#     for(let j=0;j<cnt&&i<charts.length;j++,i++){
#       const ch=charts[i];
#       const card=document.createElement('div'); card.className='chart-card';
#       card.style.animationDelay=(i*.07)+'s';
#       // pick accent color
#       const accent=COLORS[i%COLORS.length];
#       card.style.setProperty('--card-accent',`linear-gradient(90deg,${accent},${COLORS[(i+2)%COLORS.length]})`);
#       card.innerHTML=`<div class="card-hdr">
#         <div class="card-title">${ch.title}</div>
#         <div class="card-badge">${ch.labels.length} ITEMS</div>
#       </div>
#       <canvas id="${ch.id}" class="ch"></canvas>`;
#       const colName=ch.col||ch.id.replace(/^(bar_|donut_|line_|hist_|area_|radar_)/,'');
#       card.addEventListener('click',()=>{
#         if(data.cat_stats[colName])openModal('cat',colName);
#         else if(data.num_stats[colName])openModal('num',colName);
#         else if(data.date_stats[colName])openModal('date',colName);
#         else openModal('summary',null);
#       });
#       row.appendChild(card);
#     }
#     cc.appendChild(row);
#   }

#   // Render each chart
#   charts.forEach((ch,idx)=>{
#     const el=document.getElementById(ch.id); if(!el)return;
#     const ac=COLORS[idx%COLORS.length];
#     const bgs=ch.labels.map((_,i)=>COLORS[(idx+i)%COLORS.length]+'bb');
#     const bds=ch.labels.map((_,i)=>COLORS[(idx+i)%COLORS.length]);
#     let cfg;

#     if(ch.type==='donut'){
#       cfg={type:'doughnut',
#         data:{labels:ch.labels,datasets:[{data:ch.values,backgroundColor:bgs,borderColor:'#fff',borderWidth:3,hoverOffset:12}]},
#         options:{...BC,cutout:'62%',animation:{animateRotate:true,duration:1400},
#           plugins:{...BC.plugins,datalabels:{display:true,color:'#fff',font:{size:10,weight:'bold'},
#             formatter:(v,ctx)=>{const t=ctx.dataset.data.reduce((a,b)=>a+b,0);return ((v/t)*100).toFixed(0)+'%'}}}}};
#     } else if(ch.type==='line'){
#       cfg={type:'line',
#         data:{labels:ch.labels,datasets:[{label:ch.title,data:ch.values,borderColor:ac,
#           backgroundColor:ac+'22',borderWidth:2.5,tension:.4,fill:true,
#           pointBackgroundColor:ac,pointBorderColor:'#fff',pointBorderWidth:2,pointRadius:4,pointHoverRadius:6}]},
#         options:{...BC,animation:{duration:1200},
#           scales:{x:{grid:{color:'#f1f5f9'},ticks:{font:{size:10}}},y:{grid:{color:'#f1f5f9'},beginAtZero:true}}}};
#     } else if(ch.type==='area'){
#       cfg={type:'line',
#         data:{labels:ch.labels,datasets:[{label:'Count',data:ch.values,borderColor:ac,
#           backgroundColor:ac+'33',borderWidth:2,tension:.5,fill:true,
#           pointBackgroundColor:ac,pointRadius:3}]},
#         options:{...BC,animation:{duration:1000},
#           plugins:{...BC.plugins,legend:{display:false}},
#           scales:{x:{grid:{color:'#f1f5f9'},ticks:{font:{size:10}}},y:{grid:{color:'#f1f5f9'},beginAtZero:true}}}};
#     } else if(ch.type==='radar'){
#       cfg={type:'radar',
#         data:{labels:ch.labels,datasets:[{label:ch.title,data:ch.values,
#           borderColor:ac,backgroundColor:ac+'33',borderWidth:2,
#           pointBackgroundColor:ac,pointBorderColor:'#fff',pointBorderWidth:2,pointRadius:4}]},
#         options:{...BC,scales:{r:{grid:{color:'#e2e8f0'},ticks:{backdropColor:'transparent',font:{size:9},stepSize:1},
#           pointLabels:{font:{size:10},color:'#334155'},angleLines:{color:'#e2e8f0'}}}}};
#     } else {
#       // bar
#       const isH=ch.labels.length>8;
#       cfg={type:'bar',
#         data:{labels:ch.labels,datasets:[{label:'Count',data:ch.values,
#           backgroundColor:bgs,borderColor:bds,borderWidth:1.5,borderRadius:8,borderSkipped:false}]},
#         options:{...BC,indexAxis:isH?'y':'x',
#           animation:{delay:ctx=>ctx.dataIndex*35,duration:700,easing:'easeOutCubic'},
#           plugins:{...BC.plugins,legend:{display:false}},
#           scales:{x:{grid:{color:'#f1f5f9'},ticks:{font:{size:10}}},
#                   y:{grid:{color:'#f1f5f9'},beginAtZero:true,ticks:{font:{size:10}}}}}};
#     }
#     const inst=new Chart(el,cfg); chartInsts.push(inst);
#   });

#   // ── COLUMN PILLS ──
#   const cpills=document.getElementById('cpills'); cpills.innerHTML='';
#   [...data.cat_cols.map(c=>({c,cls:'pill-cat',t:'cat'})),
#    ...data.num_cols.map(c=>({c,cls:'pill-num',t:'num'})),
#    ...data.date_cols.map(c=>({c,cls:'pill-date',t:'date'}))
#   ].forEach(({c,cls,t})=>{
#     const p=document.createElement('span'); p.className=`pill ${cls}`; p.textContent=c;
#     p.addEventListener('click',()=>openModal(t,c)); cpills.appendChild(p);
#   });

#   // ── TABLE ──
#   document.getElementById('rbadge').textContent=data.total_rows.toLocaleString()+' ROWS';
#   const dtbl=document.getElementById('dtbl');
#   dtbl.innerHTML='<thead><tr>'+data.table_cols.map(c=>`<th>${c}</th>`).join('')+'</tr></thead><tbody>'+
#     data.table_rows.map(r=>'<tr>'+r.map(v=>`<td title="${v}">${v}</td>`).join('')+'</tr>').join('')+'</tbody>';

#   // ── MISSING ──
#   const mchrt=document.getElementById('mchrt');
#   if(!data.missing.cols.length){
#     mchrt.innerHTML='<div style="padding:20px;text-align:center;color:#10b981;font-weight:700;font-size:16px">✅ No Missing Data!</div>';
#   } else {
#     mchrt.innerHTML=data.missing.cols.map((c,i)=>`
#       <div class="mbar-item">
#         <div class="mbar-top"><span>${c}</span><span class="mbar-pct">${data.missing.pcts[i]}%</span></div>
#         <div class="mbar-bg"><div class="mbar-fill" style="width:0%" data-w="${data.missing.pcts[i]}%"></div></div>
#       </div>`).join('');
#     setTimeout(()=>document.querySelectorAll('.mbar-fill').forEach(b=>b.style.width=b.dataset.w),350);
#   }

#   // ── COL SUMMARY ──
#   const csum=document.getElementById('csum');
#   const groups=[['📝 Text Columns',data.cat_cols,'#1d4ed8'],['🔢 Numeric',data.num_cols,'#7c3aed'],['📅 Date',data.date_cols,'#f59e0b']];
#   csum.innerHTML=groups.filter(([,v])=>v.length).map(([k,v,color])=>`
#     <div style="margin-bottom:16px">
#       <div style="font-size:11px;font-weight:700;color:${color};letter-spacing:.5px;text-transform:uppercase;margin-bottom:8px">${k} (${v.length})</div>
#       <div style="display:flex;flex-wrap:wrap;gap:6px">${v.map(c=>`<span style="background:${color}15;border:1px solid ${color}44;border-radius:6px;padding:2px 9px;font-size:11px;color:${color};font-weight:500">${c}</span>`).join('')}</div>
#     </div>`).join('');
# }

# // ── WORLD MAP (using Chart.js choropleth-style) ──
# function renderWorldMap(mapData){
#   // Build a beautiful bubble map since geo plugin may not load
#   const el=document.getElementById('world-map-canvas');

#   // Map country names to rough lat/lng for bubble positions
#   const COUNTRY_POS={
#     'Thailand':[13.7,100.5],'Nepal':[28.3,84.1],'Brazil':[-14.2,-51.9],'Bangladesh':[23.7,90.4],
#     'USA':[37.1,-95.7],'Portugal':[39.4,-8.2],'Myanmar':[19.2,96.9],'Poland':[51.9,19.1],
#     'Denmark':[56.3,9.5],'Mexico':[23.6,-102.5],'India':[20.6,78.9],'China':[35.9,104.2],
#     'Germany':[51.2,10.4],'France':[46.2,2.2],'UK':[55.4,-3.4],'Japan':[36.2,138.2],
#     'Australia':[-25.3,133.8],'Canada':[56.1,-106.3],'Russia':[61.5,105.3],'South Africa':[-30.6,22.9],
#     'Egypt':[26.8,30.8],'Nigeria':[9.1,8.7],'Kenya':[-0.0,37.9],'Ethiopia':[9.1,40.5],
#     'Argentina':[-38.4,-63.6],'Colombia':[4.6,-74.3],'Chile':[-35.7,-71.5],'Peru':[-9.2,-75.0],
#     'Indonesia':[-0.8,113.9],'Vietnam':[14.1,108.3],'Philippines':[12.9,121.8],'Malaysia':[4.2,108.0],
#     'Pakistan':[30.4,69.3],'Sri Lanka':[7.9,80.7],'Iran':[32.4,53.7],'Saudi Arabia':[24.0,44.5],
#     'UAE':[24.0,53.8],'Turkey':[38.9,35.2],'Italy':[41.9,12.6],'Spain':[40.5,-3.7],
#     'Netherlands':[52.1,5.3],'Belgium':[50.5,4.5],'Sweden':[60.1,18.6],'Norway':[60.5,8.5],
#     'Finland':[61.9,25.7],'Switzerland':[46.8,8.2],'Austria':[47.5,14.6],'Czech Republic':[49.8,15.5],
#     'Romania':[45.9,24.9],'Hungary':[47.2,19.5],'Greece':[39.1,21.8],'Ukraine':[49.0,31.2],
#     'Morocco':[31.8,-7.1],'Tanzania':[-6.4,34.9],'Ghana':[7.9,-1.0],'Senegal':[14.5,-14.5],
#     'Cambodia':[11.5,104.9],'Laos':[19.8,102.5],'Mongolia':[46.8,103.8],'Kazakhstan':[48.0,68.0],
#   };

#   // Scatter chart simulating map
#   const pts=mapData.countries.map((c,i)=>{
#     const pos=COUNTRY_POS[c]||[Math.random()*140-50,Math.random()*320-150];
#     return {x:pos[1],y:pos[0],r:Math.max(6,Math.min(35,Math.sqrt(mapData.counts[i])*4)),
#       label:c,count:mapData.counts[i]};
#   });

#   if(mapInst){mapInst.destroy();mapInst=null}
#   mapInst=new Chart(el,{
#     type:'bubble',
#     data:{datasets:[{
#       label:'Issues by Country',
#       data:pts,
#       backgroundColor:pts.map((_,i)=>COLORS[i%COLORS.length]+'99'),
#       borderColor:pts.map((_,i)=>COLORS[i%COLORS.length]),
#       borderWidth:2,
#     }]},
#     options:{
#       responsive:true,maintainAspectRatio:false,
#       scales:{
#         x:{min:-180,max:180,grid:{color:'#f0f4ff'},ticks:{font:{size:9},color:'#94a3b8'},
#           title:{display:true,text:'Longitude',color:'#94a3b8',font:{size:10}}},
#         y:{min:-70,max:80,grid:{color:'#f0f4ff'},ticks:{font:{size:9},color:'#94a3b8'},
#           title:{display:true,text:'Latitude',color:'#94a3b8',font:{size:10}}}
#       },
#       plugins:{
#         legend:{display:false},
#         tooltip:{...BC.plugins.tooltip,
#           callbacks:{label:ctx=>`${ctx.raw.label}: ${ctx.raw.count} issues`}}
#       }
#     }
#   });

#   // Legend
#   const leg=document.getElementById('map-legend');
#   leg.innerHTML=mapData.countries.slice(0,10).map((c,i)=>
#     `<span style="display:flex;align-items:center;gap:4px;white-space:nowrap">
#       <span style="width:10px;height:10px;border-radius:50%;background:${COLORS[i%COLORS.length]};display:inline-block"></span>
#       <span>${c} (${mapData.counts[i]})</span>
#     </span>`).join('');
# }

# function renderCountryBar(mapData){
#   const el=document.getElementById('country-bar');
#   new Chart(el,{
#     type:'bar',
#     data:{
#       labels:mapData.countries.slice(0,12),
#       datasets:[{label:'Issues',data:mapData.counts.slice(0,12),
#         backgroundColor:COLORS.slice(0,12).map(c=>c+'cc'),
#         borderColor:COLORS.slice(0,12),borderWidth:1.5,borderRadius:8,borderSkipped:false}]
#     },
#     options:{...BC,indexAxis:'y',maintainAspectRatio:false,
#       animation:{delay:ctx=>ctx.dataIndex*60,duration:900,easing:'easeOutCubic'},
#       plugins:{...BC.plugins,legend:{display:false}},
#       scales:{x:{grid:{color:'#f1f5f9'},ticks:{font:{size:11}}},
#               y:{grid:{display:false},ticks:{font:{size:11}}}}}
#   });
# }
# </script>
# </body>
# </html>"""

# # ── ROUTES ───────────────────────────────────
# @app.route('/')
# def index():
#     return render_template_string(HTML)

# @app.route('/analyze', methods=['POST'])
# def analyze_route():
#     payload = request.get_json()
#     try:
#         if payload['type'] == 'file':
#             raw  = base64.b64decode(payload['data'])
#             name = payload.get('name','file.xlsx').lower()
#             df   = pd.read_csv(io.BytesIO(raw)) if name.endswith('.csv') else load_excel(raw)
#         elif payload['type'] == 'gsheet':
#             df = load_gsheet(payload['url'])
#         else:
#             return jsonify({'error': 'Unknown type'})
#         return jsonify(analyze(df))
#     except Exception as e:
#         return jsonify({'error': str(e)})

# # ── START ────────────────────────────────────
# def open_browser():
#     import time; time.sleep(1.2)
#     webbrowser.open('http://localhost:5050')

# if __name__ == '__main__':
#     print("""
# ╔══════════════════════════════════════════════════════╗
# ║   ⚡ ISSUES COMMAND NEXUS v3 — Starting...           ║
# ║   🌐 Browser: http://localhost:5050                  ║
# ║   📂 Upload Excel/CSV  OR  🔗 Google Sheet URL       ║
# ║   🌍 World Map + Premium Charts + Click Details      ║
# ╚══════════════════════════════════════════════════════╝
#     """)
#     threading.Thread(target=open_browser, daemon=True).start()
#     app.run(port=5050, debug=False)





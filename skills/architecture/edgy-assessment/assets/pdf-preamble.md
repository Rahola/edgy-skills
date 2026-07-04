---
pdf_options:
  margin: 15mm 20mm 15mm 20mm
  headerTemplate: '<div></div>'
  footerTemplate: '<div style="font-size:8px;text-align:center;width:100%;color:#888;">{{COMPANY}} — {{FOOTER_LABEL}} | <span class="pageNumber"></span> / <span class="totalPages"></span></div>'
  displayHeaderFooter: true
---

<style>
  .edgy-badge { display: inline-block; padding: 3px 10px; font-weight: bold; font-size: 0.85em; color: #222; margin: 1px 2px; }
  /* Outcome = rounded pill */
  .edgy-purpose { background: #80ffb7; border-radius: 12px; }
  .edgy-capability { background: #a6c0ff; border-radius: 12px; }
  .edgy-task { background: #ff99bd; border-radius: 12px; }
  /* Activity = pentagon arrow (clip-path) */
  .edgy-story { background: #80ffb7; clip-path: polygon(0% 0%, 85% 0%, 100% 50%, 85% 100%, 0% 100%); padding-right: 18px; border-radius: 0; }
  .edgy-process { background: #a6c0ff; clip-path: polygon(0% 0%, 85% 0%, 100% 50%, 85% 100%, 0% 100%); padding-right: 18px; border-radius: 0; }
  .edgy-journey { background: #ff99bd; clip-path: polygon(0% 0%, 85% 0%, 100% 50%, 85% 100%, 0% 100%); padding-right: 18px; border-radius: 0; }
  /* Object = sharp rectangle */
  .edgy-content { background: #80ffb7; border-radius: 2px; }
  .edgy-asset { background: #a6c0ff; border-radius: 2px; }
  .edgy-channel { background: #ff99bd; border-radius: 2px; }
  .edgy-brand { background: #ffd580; border-radius: 2px; }
  .edgy-product { background: #e599ff; border-radius: 2px; }
  .edgy-organisation { background: #80eaff; border-radius: 2px; }
  .edgy-map { display: flex; flex-wrap: wrap; gap: 8px; margin: 12px 0; }
  .edgy-card { padding: 10px 14px; font-size: 0.9em; color: #222; flex: 1 1 200px; min-width: 180px; }
  .edgy-card b { display: block; margin-bottom: 4px; }
  .edgy-card.outcome { border-radius: 16px; }
  .edgy-card.activity { border-radius: 0; clip-path: polygon(0% 0%, 85% 0%, 100% 50%, 85% 100%, 0% 100%); padding-right: 30px; }
  .edgy-card.object { border-radius: 2px; }
  .edgy-section { border-left: 4px solid; padding-left: 12px; margin: 16px 0; }
  .edgy-section.identity { border-color: #80ffb7; }
  .edgy-section.architecture { border-color: #a6c0ff; }
  .edgy-section.experience { border-color: #ff99bd; }
  .edgy-section.intersection { border-color: #e599ff; }
  .edgy-rel { font-size: 0.85em; color: #555; font-style: italic; }
  .coherence-strong { background: #d4edda; padding: 4px 10px; border-radius: 4px; font-weight: bold; }
  .coherence-good { background: #fff3cd; padding: 4px 10px; border-radius: 4px; font-weight: bold; }
  .coherence-weak { background: #f8d7da; padding: 4px 10px; border-radius: 4px; font-weight: bold; }
  .legend { display: flex; flex-wrap: wrap; gap: 10px; margin: 14px 0 20px 0; padding: 12px 16px; background: #f8f9fa; border-radius: 8px; border: 1px solid #e0e0e0; font-size: 0.85em; }
  .legend-item { display: flex; align-items: center; gap: 6px; }
  .legend-dot { width: 16px; height: 16px; border-radius: 4px; display: inline-block; border: 1px solid rgba(0,0,0,0.1); }
  .meta-table { font-size: 0.9em; margin: 8px 0 16px 0; }
  .meta-table td { padding: 2px 12px 2px 0; vertical-align: top; }
  .meta-table td:first-child { font-weight: bold; color: #555; white-space: nowrap; }
</style>

# {{COMPANY}} — {{REPORT_TITLE}}

<table class="meta-table">
  <tr><td>{{SOURCE_LABEL}}</td><td>{{SOURCE}}</td></tr>
  <tr><td>{{METHOD_LABEL_FIELD}}</td><td>{{METHOD_LABEL}}</td></tr>
  <tr><td>{{ANALYST_LABEL}}</td><td>{{ANALYST}}</td></tr>
</table>

<div class="legend">
  <div class="legend-item"><span class="legend-dot" style="background:#80ffb7"></span> {{LEGEND_IDENTITY}}</div>
  <div class="legend-item"><span class="legend-dot" style="background:#a6c0ff"></span> {{LEGEND_ARCHITECTURE}}</div>
  <div class="legend-item"><span class="legend-dot" style="background:#ff99bd"></span> {{LEGEND_EXPERIENCE}}</div>
  <div class="legend-item"><span class="legend-dot" style="background:#ffd580"></span> {{LEGEND_BRAND}}</div>
  <div class="legend-item"><span class="legend-dot" style="background:#e599ff"></span> {{LEGEND_PRODUCT}}</div>
  <div class="legend-item"><span class="legend-dot" style="background:#80eaff"></span> {{LEGEND_ORGANISATION}}</div>
</div>

<div style="font-size:0.8em; color:#666; margin: -10px 0 16px 0;">
  <b>{{BADGE_LABEL}}</b>
  <span style="display:inline-block; background:#ddd; border-radius:12px; padding:2px 10px; margin:0 4px;">{{SHAPE_LABEL_OUTCOME}}</span> {{SHAPE_DESC_OUTCOME}}
  <span style="display:inline-block; background:#ddd; clip-path:polygon(0% 0%, 80% 0%, 100% 50%, 80% 100%, 0% 100%); padding:2px 16px 2px 8px; margin:0 4px;">{{SHAPE_LABEL_ACTIVITY}}</span> {{SHAPE_DESC_ACTIVITY}}
  <span style="display:inline-block; background:#ddd; border-radius:2px; padding:2px 10px; margin:0 4px;">{{SHAPE_LABEL_OBJECT}}</span> {{SHAPE_DESC_OBJECT}}
</div>

{{EDGY_INTRO}}

<!-- BEGIN ANALYSIS BODY (template-specific content below) -->

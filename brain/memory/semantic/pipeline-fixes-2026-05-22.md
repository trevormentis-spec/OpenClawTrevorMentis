# pipeline-fixes-2026-05-22

## 2026-05-22

All 8 pipeline fixes applied on 2026-05-22:

Issue 1 - models_used: Fixed exec_prompt() defaults and mock_exec() in analyze.py to use 'deepseek/deepseek-v4-pro' instead of 'deepseek/deepseek-v4-flash' and 'anthropic/claude-opus-4.7'

Issue 2 - South America feeds: Tested 80+ feed URLs. Replaced dead URLs with working alternatives: MercoPress -> /rss/latin-america, Batimes -> /feed, added Infobae, Dialogo Americas, El Nacional Venezuela, Agencia Brasil PT, Folha PT. Removed WOLA, Wilson Center, Americas Quarterly, The Brazilian Report, O Globo, El Mercurio, La Nacion AR, El Comercio PE, El Universal MX (all 404/403/broken).

Issue 3+8 - Source URLs: Added 'url' field to incident level in normalise(), web_search_fallback, and social_media_collect. Updated deliver_text_brief.py to build incident_id->URL lookup and include clickable hyperlinks in HTML output.

Issue 4 - Central Asia: Reduced to ONLY 5 Stans (Kazakhstan, Kyrgyzstan, Tajikistan, Turkmenistan, Uzbekistan). Removed Russia, China, Japan, India, Pakistan, etc. Updated WEB_SEARCH_REGIONS and SOCIAL_MEDIA_QUERIES accordingly.

Issue 5 - Email intel: Added collect_email_intel.py call to orchestrator between collector and analyst steps.

Issue 6 - Substack feeds: Removed 15 broken Substack feeds (404/BAD_XML). Kept 20+ working ones. Tested all.

Issue 7 - HEARTBEAT: Reviewed HEARTBEAT.md. System exists and last ran 2026-05-20. heartbeat-state.json file doesn't exist (needs re-creation by next heartbeat cycle). Collection cycle available via collection-cycle.sh.

All 4 Python files pass compilation checks.

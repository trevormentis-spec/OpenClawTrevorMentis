# Social Monitor — runs on shorter cadence than the daily brief
# Scheduled via OpenClaw cron, polls Reddit/Bluesky for Mexico keywords
# Every 4 hours during waking hours (12:00, 16:00, 20:00 PT)
# Logs to tasks/social_monitor_state.json
cd /home/ubuntu/.openclaw/workspace
python3 scripts/social_monitor.py --keywords "CJNG,Sinaloa,Sheinbaum,USMCA,cartel,fentanyl" --platform all

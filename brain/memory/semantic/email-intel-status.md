# email-intel-status

## 2026-05-22

Email intel from Gmail/AgentMail newsletters is wired into the orchestrator. Script: scripts/collect_email_intel.py. Reads AgentMail inbox (trevor_mentis@agentmail.to) AND Gmail inbox (trevor.mentis@gmail.com via Maton gateway) for newsletters from CTP/ISW, Cipher Brief, Foreign Policy, InSight Crime, Americas Brief, etc. Incidents injected into collector output before analysis. Currently reading 34+ newsletter sources from AgentMail inbox. Verified working: 27 incidents injected on 2026-05-22.

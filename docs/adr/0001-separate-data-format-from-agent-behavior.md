# Separate Data Format from Agent Behavior in timeline skill

The timeline skill's SKILL.md defines **only data format and integrity constraints** (file naming, section structure, Todo/Event/Note schema, sorting rules). All agent-specific behavior—trigger words, operation flows, time parsing rules, cron job configuration, user preferences—belongs in the user project's AGENTS.md. Hermes should modify AGENTS.md to adapt behavior, never SKILL.md.

This separation ensures timeline skill remains platform-agnostic and reusable across different agents. The trade-off: cron jobs now trigger the skill directly (LLM cost) instead of running scripts via `no_agent` mode. Accepted for architectural simplicity and unified handling.
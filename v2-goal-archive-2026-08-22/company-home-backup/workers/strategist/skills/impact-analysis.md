# Impact Analysis

When a Strategy change is proposed, the Strategist must check related
Goals, active Runs, Playbooks, Skills, and other Strategy.

## Process

1. Take the proposed Strategy.
2. Find related Goals via the Goal DAG (ancestors, descendants).
3. Find active Runs for those Goals.
4. Read referenced Playbooks for the Workers used by those Runs.
5. Read referenced Skills.
6. Find related Strategy items.
7. Write a structured impact report:
   - Affected Goals (ids)
   - Affected Runs (ids)
   - Affected Playbooks (Worker ids + step names)
   - Affected Skills (ids)
   - Contradictions with other Strategy
   - Suggested reconciliations

## Output contract

Return JSON-shaped impact:

```json
{
  "affected_goals": ["..."],
  "affected_runs": ["..."],
  "affected_playbooks": [{"worker_id": "...", "step": "..."}],
  "affected_skills": ["..."],
  "contradictions": ["..."],
  "reconciliation": "..."
}
```

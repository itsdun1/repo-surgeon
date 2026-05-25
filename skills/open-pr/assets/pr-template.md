## What changed

- {{ what_bullet_1 }}
- {{ what_bullet_2 }}
- {{ what_bullet_3 }}

## Why

{{ why_paragraph }}

## How I tested

- {{ test_command_1 }} → {{ test_outcome_1 }}
- {{ test_command_2 }} → {{ test_outcome_2 }}

## Risk

**{{ risk_level }}**: {{ risk_explanation }}

## Sources

- Issue: #{{ issue_number }}
{% if related_prs %}
- Related PRs: {{ related_prs_list }}
{% endif %}
{% if memory_entries %}
- Memory entries cited:
{% for entry in memory_entries %}
  - `{{ entry }}`
{% endfor %}
{% endif %}

---

*This PR was opened by [Repo Surgeon](https://github.com/{{ agent_repo }}), an autonomous coding agent built on the [GitAgent Protocol](https://github.com/open-gitagent). Memory updates from this session: {{ memory_diff_summary }}.*

*Human review required before merge.*

# base_statements_stacks.md
> Organic source of truth for stack selection (human-written)

```json
{
  "project": "WPC2_Zero_Prompts_Demo",
  "default_stack": {
    "markup": "HTML5",
    "style": "SCSS3",
    "script": "Vanilla JS",
    "note": "Always suggest this first"
  },
  "user_override": null,
  "rules": [
    "Agent-Plan must ask the user for stack confirmation",
    "Default suggestion is always HTML5 + SCSS3 + Vanilla JS",
    "If user chooses different stack → obey and update user_override",
    "Never force the default if user has chosen otherwise",
    "Record final approved stack here before Execution starts"
  ],
  "approved_stack": null,
  "approved_by_jev": false,
  "confidence": null
}
```

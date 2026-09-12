# Visual review contract

Review all supplied Blender render views together with the structural scene state and task requirements.

Do not infer exact dimensions, object names, topology or transforms from pixels when those facts are available in structured scene state.

Evaluate:

- framing and camera composition;
- visible geometry defects;
- intersections/floating objects;
- material plausibility and consistency;
- lighting/exposure/readability;
- style adherence;
- cross-view consistency;
- obvious missing scene content.

Return a concise structured result conceptually equivalent to:

```json
{
  "accepted": false,
  "problems": [
    {
      "category": "camera",
      "severity": "high",
      "evidence": "The subject is cropped in the hero view.",
      "suggested_fix": "Adjust the durable camera configuration."
    }
  ],
  "source_changes": [
    {
      "file": "config/workflow.yaml",
      "path": "cameras[0]",
      "reason": "Recover complete framing."
    }
  ]
}
```

A visual improvement made only in a live Blender session is not accepted as completion. The durable source must be updated and rebuilt.

# Training Evidence

This directory stores detector evidence reports that teach the workbench something about My Singing Monsters screenshots.

Detector evidence reports are training artifacts, not disposable logs. A useful report may show a confirmed Breeding Structure, a false positive, a missed detection, or parent egg crops that were aimed badly. All of those cases help tune future detector behavior.

Useful evidence includes:

- confirmed positives
- false positives
- missed detections
- bad parent egg crops
- corrected parent egg crops
- manual confirmation of parents or result

Generated evidence should only be deleted when it is accidental, duplicate, or mechanically broken. If a report captures a real detector behavior that should be learned from, keep it and annotate it.

Human confirmation and correction are authoritative. Use the `training_review` block in each report as the durable annotation area.

Suggested `detector_classification` values:

- `confirmed_positive`
- `false_positive`
- `missed_detection`
- `parent_crop_incorrect`
- `parent_crop_correct`
- `unresolved`

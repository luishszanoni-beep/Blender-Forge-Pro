# Rigging Specialist | Acceptance Checklist

- [ ] User explicitly requested rig or animation.
- [ ] Skeleton/pivot plan reflects actual part semantics.
- [ ] Rest pose and scale/rotation transforms consistent.
- [ ] Skin weights bounded and reviewed on stress poses.
- [ ] Rig does not mutate approved unposed silhouette.
- [ ] Export target supports chosen bone/constraint strategy.
- [ ] Pose QA images recorded with explicit scene states.
- [ ] G6 skip state used for static-only tasks.

When any required item is unchecked, record a blocker or explicit `PENDING`/`UNKNOWN`; do not invent a passing test.

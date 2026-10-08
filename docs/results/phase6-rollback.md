# Phase 6 - v2-bad Automatic Rollback

## Canary
Model: v2-bad
Canary traffic: 10%

## Accuracy Gate
Required accuracy: >= 85%

Observed:
- Measurement 1: 36.84%
- Measurement 2: 38.10%

Result: FAILED

## Latency Gate
Observed:
- 8.69 ms
- 8.63 ms

Result: PASSED

## Error Rate Gate
Observed:
- 0%
- 0%

Result: PASSED

## Rollback

The accuracy metric failed twice.
Failure limit: 1.

Argo Rollouts automatically aborted revision 16.

v2-bad was scaled down and stable v3-good remained active.

## Conclusion

The system successfully detected a degraded ML model using live labeled traffic and automatically rolled back the canary release.

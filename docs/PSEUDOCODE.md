# EARP — Algorithm Pseudocode Pack

Design-stage paperwork for the Enterprise AI Reliability Platform v1.

**Status:** derived from the running code at commit `0543498` on 2026-11-12.
This pack is *descriptive*, not aspirational: every algorithm below was read
out of the source line by line and is traceable to a file and line range in
the table under [Traceability](#traceability). Nothing here describes
behaviour the repository does not have.

**Why it exists.** The repo shipped v0.3.0 without a design-stage artifact.
The project's own SDLC discipline puts pseudocode before implementation; this
file closes that gap after the fact and gives the eight load-bearing
algorithms a reviewable form that a compliance reader can audit without
reading Python.

---

## Scope

**In scope.** The eight algorithms that carry a decision, a number, or a
proof obligation: reliability math, the weighted composite score, the NIST
AI RMF policy gate, the hash-chained audit ledger and its verifier, release
approval with separation of duties, anomaly detection, and retention /
legal-hold eligibility.

**Out of scope.** CRUD list/get helpers, FastAPI routing and dependency
wiring, Pydantic field validation (stated as preconditions here, not
re-derived), SQLAlchemy session mechanics, the React frontend, report
rendering, and the retired `src/` prototype.

**Acceptance criteria.** Each algorithm names its INPUT, OUTPUT, and at
least one INVARIANT or POSTCONDITION; carries its source file and line
range; uses no language syntax; and states every hard stop explicitly
rather than burying it in a branch.

---

## Notation

| Symbol | Meaning |
|---|---|
| `←` | assignment |
| `=` / `≠` | comparison |
| `//` | margin comment |
| `ASSERT` | proof obligation — a failed ASSERT is a defect, never passed over |
| `STOP → ...` | hard stop; control leaves the algorithm here |
| `CALL` | invokes another algorithm or subroutine in this pack |
| `NOW_UTC` | the current instant, timezone-aware, UTC |
| `NONE` | absent value (`None` / SQL `NULL`) |

Keywords are capitalised. Steps are numbered, one action per line, four
spaces per nesting level.

---

## Traceability

| # | Algorithm | Source | Lines |
|---|---|---|---|
| A1 | ComputeReliability | `enterprise_ai_backend/app/services.py` | 15–37 |
| A2 | ComputeReliabilityScore | `enterprise_ai_backend/app/services.py` | 78–140 |
| A3 | EvaluatePolicyGate | `enterprise_ai_backend/app/services.py` | 437–534 |
| A4 | AppendAuditEvent | `enterprise_ai_backend/app/services.py` | 693–770 |
| A5 | VerifyAuditChain | `enterprise_ai_backend/app/services.py` | 824–870 |
| A6 | ApproveReleaseApproval | `enterprise_ai_backend/app/services.py` | 1069–1190 |
| A7 | DetectAnomaliesFromHistory | `enterprise_ai_backend/app/ml.py` | 18–77 |
| A8 | RetentionStatus | `enterprise_ai_backend/app/services.py` | 1001–1043 |

Shared policy constants (`FUNCTION_WEIGHTS`, tier thresholds) are declared
twice on purpose: `libs/policy/scoring.py:21-34` is the auditable copy for
compliance reviewers, re-stated at `services.py:1200-1214`. A4 and A6 both
depend on `sha256_of` at `services.py:1193`.

---

## A1 — ComputeReliability

Textbook anchor: the exponential reliability function under a constant
failure rate (constant-hazard model), `R(t) = e^(-lambda*t)`.

```text
ALGORITHM ComputeReliability
SOURCE:  enterprise_ai_backend/app/services.py:15-37
INPUT:   mtbf_hours > 0, mttr_hours > 0, mission_time_hours > 0
OUTPUT:  persisted record {availability, reliability,
                           failure_rate_per_hour, expected_failures}
INVARIANT:     0 < availability < 1   AND   0 < reliability <= 1
POSTCONDITION: exactly one new ReliabilityComputation row exists

1. ASSERT mtbf_hours > 0 AND mttr_hours > 0 AND mission_time_hours > 0
                                            // enforced upstream by schema gt=0
2. availability ← mtbf_hours / (mtbf_hours + mttr_hours)
3. failure_rate ← 1 / mtbf_hours                        // lambda, per hour
4. reliability ← EXP( -mission_time_hours / mtbf_hours ) // R(t) = e^(-lambda*t)
5. expected_failures ← mission_time_hours / mtbf_hours   // lambda * t
6. record ← NEW ReliabilityComputation
    6.1 record.availability ← ROUND(availability, 8)
    6.2 record.reliability ← ROUND(reliability, 8)
    6.3 record.failure_rate_per_hour ← ROUND(failure_rate, 10)
    6.4 record.expected_failures ← ROUND(expected_failures, 8)
7. CALL persist(record)
8. RETURN record
```

---

## A2 — ComputeReliabilityScore

```text
ALGORITHM ComputeReliabilityScore
SOURCE:  enterprise_ai_backend/app/services.py:78-140
INPUT:   system_name,
         components[] each = (name, value in [0,1], weight in (0,1],
                              nist_function or NONE)
OUTPUT:  {composite_score in [0,100], tier, weights_normalized,
          nist_breakdown, components, computed_at}
INVARIANT:     total_weight > 0
POSTCONDITION: composite_score = 100 * (SUM value*weight) / (SUM weight)

1. total_weight ← SUM of component.weight FOR EACH component
2. IF total_weight <= 0 THEN
    2.1 STOP → raise "Total component weight must be positive."
3. weights_normalized ← NOT ( total_weight is within 1e-6 of 1.0 )
4. composite_01 ← ( SUM of component.value * component.weight ) / total_weight
5. composite_100 ← ROUND(composite_01 * 100, 4)
6. tier ← CALL TierFromComposite(composite_100)
7. by_function ← empty list for each of govern, map, measure, manage
8. FOR EACH component
    8.1 IF component.nist_function ≠ NONE THEN
        8.1.1 APPEND (component.value, component.weight)
              TO by_function[component.nist_function]
9. FOR EACH fn IN (govern, map, measure, manage)
    9.1 breakdown[fn] ← CALL WeightedAverage(by_function[fn])
                                            // NONE when that group is empty
10. output ← {system_name, composite_100, tier, weights_normalized,
              breakdown, components, NOW_UTC}
11. IF a database session was supplied THEN
    11.1 CALL PersistScoreRecord(output)    // feeds /reliability/score/history
12. RETURN output


SUBROUTINE TierFromComposite(c)
SOURCE:  enterprise_ai_backend/app/services.py:57-63
1. IF c >= 80 THEN RETURN "LOW"
2. ELSE IF c >= 60 THEN RETURN "MEDIUM"
3. ELSE RETURN "HIGH"


SUBROUTINE WeightedAverage(pairs)
SOURCE:  enterprise_ai_backend/app/services.py:65-76
OUTPUT:  a 0-100 value, or NONE when nothing was supplied
1. IF pairs is empty THEN RETURN NONE
2. total_w ← SUM of w FOR EACH (v, w) IN pairs
3. IF total_w <= 0 THEN RETURN NONE
4. RETURN ROUND( ( SUM of v * w ) / total_w * 100, 4 )
```

---

## A3 — EvaluatePolicyGate

Worst severity wins. A function the caller never tagged is *not scored*, and
is therefore not failed — step 7.2 is the whole of that decision.

```text
ALGORITHM EvaluatePolicyGate
SOURCE:  enterprise_ai_backend/app/services.py:449-534
         decision rule at :437-448, severity order at :430-435
INPUT:   score (output of A2),
         thresholds (defaults: allow_min 80, warn_min 60, nist_floor 40)
OUTPUT:  {decision in (allow, warn, block), composite_score, tier,
          reasons[], thresholds_applied, evaluated_at}
INVARIANT:     reasons is never empty - the composite band always adds one
POSTCONDITION: decision = the worst severity present in reasons

1. IF thresholds not supplied THEN thresholds ← DEFAULTS
2. reasons ← empty list
3. c ← score.composite_score
4. IF c >= thresholds.allow_min_composite THEN
    4.1 APPEND reason("composite_meets_allow", severity INFO)
5. ELSE IF c >= thresholds.warn_min_composite THEN
    5.1 APPEND reason("composite_below_allow", severity WARN)
6. ELSE
    6.1 APPEND reason("composite_below_warn", severity BLOCK)
7. FOR EACH fn IN (govern, map, measure, manage)
    7.1 val ← score.nist_breakdown[fn]
    7.2 IF val = NONE THEN CONTINUE         // untagged is unscored, not failed
    7.3 IF val < thresholds.min_nist_function_score THEN
        7.3.1 APPEND reason("nist_<fn>_below_floor", severity BLOCK)
8. SORT reasons BY severity                 // BLOCK first, then WARN, then INFO
9. decision ← CALL OverallDecision(reasons)
10. RETURN {score.system_name, decision, c, score.tier,
            reasons, thresholds, NOW_UTC}


SUBROUTINE OverallDecision(reasons)
SOURCE:  enterprise_ai_backend/app/services.py:437-448
1. severities ← the set of reason.severity FOR EACH reason
2. IF BLOCK IN severities THEN RETURN block          // one block is enough
3. IF WARN IN severities THEN RETURN warn
4. RETURN allow
```

---

## A4 — AppendAuditEvent

Append-only: no prior row is ever read for update. Each row commits to its
predecessor's hash, so altering any earlier row invalidates every hash from
that point forward.

```text
ALGORITHM AppendAuditEvent
SOURCE:  enterprise_ai_backend/app/services.py:728-770
INPUT:   event_type, entity_type, entity_key, actor_email, payload
OUTPUT:  new AuditLogRecord with previous_hash and record_hash set
INVARIANT:     previous_hash of row N = record_hash of row N-1
POSTCONDITION: no existing row was modified

1. latest ← the AuditLogRecord with the greatest id, or NONE if table is empty
2. IF latest = NONE THEN previous_hash ← NONE        // genesis row
3. ELSE previous_hash ← latest.record_hash
4. created_at ← NOW_UTC
5. payload_json ← CANONICAL_JSON(payload or empty object)
6. record_hash ← CALL AuditRecordHash(previous_hash, event_type, entity_type,
                                      entity_key, actor_email,
                                      payload_json, created_at)
7. record ← NEW AuditLogRecord carrying all of the above
8. CALL persist(record)
9. RETURN record


SUBROUTINE AuditRecordHash(previous_hash, event_type, entity_type,
                           entity_key, actor_email, payload_json, created_at)
SOURCE:  enterprise_ai_backend/app/services.py:703-726
1. fields ← {
       previous_hash : previous_hash or ""   // NONE and "" hash identically
       event_type    : event_type
       entity_type   : entity_type
       entity_key    : entity_key or ""
       actor_email   : actor_email or ""
       payload_json  : payload_json
       created_at    : created_at as UTC, timezone dropped,
                       ISO-8601 to microsecond precision
   }
2. RETURN SHA256( CANONICAL_JSON(fields) )


SUBROUTINE CANONICAL_JSON(value)
SOURCE:  enterprise_ai_backend/app/services.py:693-694
POSTCONDITION: one byte string per field set, independent of insertion order
1. RETURN JSON of value with keys sorted, no whitespace between tokens,
          and any non-JSON value rendered as its text form
```

---

## A5 — VerifyAuditChain

Step 4.4 is the design decision worth defending: the walk advances on the
**stored** hash, not the recomputed one. A single tampered row therefore
reports its own mismatch instead of cascading one into every later row — the
verifier localises damage rather than just detecting it.

```text
ALGORITHM VerifyAuditChain
SOURCE:  enterprise_ai_backend/app/services.py:824-870
INPUT:   the whole AuditLogRecord table
OUTPUT:  {chain_valid, checked_records, latest_hash, issues[]}
INVARIANT:     rows are walked in ascending id order - append order
POSTCONDITION: chain_valid = TRUE if and only if issues is empty

1. rows ← ALL AuditLogRecord ORDERED BY id ASCENDING
2. issues ← empty list
3. previous_hash ← NONE                     // expected link for the first row
4. FOR EACH row IN rows
    4.1 IF row.previous_hash ≠ previous_hash THEN
        4.1.1 APPEND issue(row.id, "previous_hash_mismatch",
                           expected previous_hash, actual row.previous_hash)
    4.2 expected_hash ← CALL AuditRecordHash(row.previous_hash, row.event_type,
                                             row.entity_type, row.entity_key,
                                             row.actor_email, row.payload_json,
                                             row.created_at)
    4.3 IF row.record_hash ≠ expected_hash THEN
        4.3.1 APPEND issue(row.id, "record_hash_mismatch",
                           expected_hash, actual row.record_hash)
    4.4 previous_hash ← row.record_hash     // advance on STORED hash, so one
                                            // bad row does not poison the rest
5. ASSERT every row was visited exactly once
6. RETURN {chain_valid : issues is empty,
           checked_records : COUNT(rows),
           latest_hash : last row's record_hash, or NONE when empty,
           issues}
```

---

## A6 — ApproveReleaseApproval

Separation of duties. Two independent lanes, and the requester can never be
the approver.

```text
ALGORITHM ApproveReleaseApproval
SOURCE:  enterprise_ai_backend/app/services.py:1148-1190
INPUT:   approval_id, approver_email, approver_role, approval_notes
OUTPUT:  the ReleaseApproval row, status now "approved"
INVARIANT:     the requester of an approval is never its approver
POSTCONDITION: on success exactly one "release.approvals.approve"
               audit event has been appended

1. record ← the ReleaseApproval with id = approval_id
2. IF record = NONE THEN STOP → raise "not_found"
3. IF record.status = "approved" THEN
    3.1 STOP → raise "already_approved"     // re-approval refused, not silent
4. IF approver_email = record.requested_by_email THEN
    4.1 STOP → raise "self_approval_forbidden"       // separation of duties
5. IF approver_role NOT IN {record.approval_type, "admin"} THEN
    5.1 STOP → raise "wrong_role"
6. record.status ← "approved"
7. record.approved_by_email ← approver_email
8. record.approval_notes ← approval_notes
9. record.approved_at ← NOW_UTC
10. CALL persist(record)
11. CALL AppendAuditEvent(event_type  = "release.approvals.approve",
                          entity_type = "release",
                          entity_key  = record.release + ":" + record.branch,
                          actor_email = approver_email,
                          payload     = the approval's identifying fields)
12. RETURN record


ALGORITHM ReleaseApprovalSummary
SOURCE:  enterprise_ai_backend/app/services.py:1069-1096
         required lanes at :1046-1050
INPUT:   release, branch
OUTPUT:  {ready_for_release, pending_approval_types[], approvals[]}
INVARIANT:     required lanes are exactly (security_lead, compliance_lead)
POSTCONDITION: ready_for_release = TRUE only when BOTH lanes are approved

1. approvals ← ALL ReleaseApproval for (release, branch)
                ORDERED BY created_at ASCENDING, id ASCENDING
2. latest_by_type ← empty map
3. FOR EACH row IN approvals
    3.1 latest_by_type[row.approval_type] ← row       // last row of a type wins
4. pending ← empty list
5. FOR EACH required IN (security_lead, compliance_lead)
    5.1 row ← latest_by_type[required]
    5.2 IF row = NONE OR row.status ≠ "approved" THEN
        5.2.1 APPEND required TO pending
6. RETURN {release, branch,
           ready_for_release : pending is empty,
           pending, approvals}
```

---

## A7 — DetectAnomaliesFromHistory

Unsupervised, and in-sample: the model is fitted on the very rows it then
scores. `contamination` therefore fixes the expected anomaly fraction before
any data is seen — it is a policy choice, not a measurement. Features are
unscaled, which Isolation Forest tolerates because it splits on thresholds
rather than distances.

```text
ALGORITHM DetectAnomaliesFromHistory
SOURCE:  enterprise_ai_backend/app/ml.py:55-77
INPUT:   the ReliabilityComputation table, contamination (default 0.1)
OUTPUT:  {n_trained_on, n_scored, predictions[], scores[],
          anomaly_count, model, record_ids[]}
INVARIANT:     at least 2 historical rows are required
POSTCONDITION: predictions[i] = -1 marks row record_ids[i] anomalous

1. rows ← ALL ReliabilityComputation
2. IF COUNT(rows) < 2 THEN
    2.1 STOP → raise "Need at least 2 historical records
                      to run anomaly detection"
3. X ← empty list of feature vectors
4. FOR EACH row IN rows
    4.1 APPEND [row.mtbf_hours, row.mttr_hours, row.mission_time_hours,
                row.availability, row.reliability] TO X    // 5 features
5. result ← CALL DetectAnomalies(X, contamination)
6. result.record_ids ← [row.id FOR EACH row IN rows]  // same order as X
7. RETURN result


SUBROUTINE DetectAnomalies(records, contamination)
SOURCE:  enterprise_ai_backend/app/ml.py:18-53
1. ASSERT records is 2-dimensional AND has at least 2 rows
2. model ← IsolationForest(n_estimators = 100,
                           contamination = contamination,
                           random_state = 42)       // fixed seed = repeatable
3. CALL model.fit(records)              // in-sample: fitted on what it scores
4. predictions ← model.predict(records)     // +1 normal, -1 anomaly
5. scores ← model.decision_function(records)         // higher = more normal
6. RETURN {n_trained_on  : row count of records,
           n_scored      : row count of records,
           predictions, scores,
           anomaly_count : COUNT of p IN predictions WHERE p = -1,
           model         : the model name and its settings}
```

---

## A8 — RetentionStatus

A legal hold is checked **before** age is considered, so a held record can
never be reported eligible however old it is. This algorithm reports
eligibility only — nothing in the local slice deletes an audit row.

```text
ALGORITHM RetentionStatus
SOURCE:  enterprise_ai_backend/app/services.py:1001-1043
         default policy at :873, current policy at :876-893
INPUT:   the AuditLogRecord table, the LegalHold table,
         the current RetentionPolicy
OUTPUT:  {generated_at, retention_days, total_audit_records,
          active_legal_holds, held_record_count, eligible_record_count,
          held_record_ids[], eligible_record_ids[]}
INVARIANT:     a record under an active hold is never reported eligible
POSTCONDITION: held_record_ids and eligible_record_ids are disjoint

1. policy ← CALL CurrentRetentionPolicy()
                        // newest row, else default 2555 days (seven years)
2. now ← NOW_UTC
3. cutoff ← now - (policy.retention_days * 86400 seconds)
4. active_holds ← ALL LegalHold WHERE released_at = NONE
5. hold_keys ← the set of (entity_type, entity_key) FOR EACH active hold
6. audit_rows ← ALL AuditLogRecord ORDERED BY id ASCENDING
7. held_ids ← empty list
8. eligible_ids ← empty list
9. FOR EACH row IN audit_rows
    9.1 row_created ← row.created_at, read as UTC when it carries no timezone
    9.2 IF (row.entity_type, row.entity_key) IN hold_keys THEN
        9.2.1 APPEND row.id TO held_ids
        9.2.2 CONTINUE              // hold decided it; age is never consulted
    9.3 IF row_created <= cutoff THEN APPEND row.id TO eligible_ids
10. ASSERT held_ids and eligible_ids share no id
11. RETURN {now, policy.retention_days, COUNT(audit_rows),
            COUNT(active_holds), COUNT(held_ids), COUNT(eligible_ids),
            held_ids, eligible_ids}

NOTE: eligibility is a report, not an action. Deleting an audit record is
      STOP → owner decides.
```

---

## Provenance

Derived by close reading of the sources named in each SOURCE line, at commit
`0543498`, on 2026-11-12. Line numbers are accurate as of that commit and
will drift as the files change; the algorithm names will not.

Two things this pack deliberately does **not** claim: that the pseudocode was
written before the code (it was not — the repo shipped first, and this is
after-the-fact design paperwork), and that any algorithm here has been
re-verified against a fresh test run in this session. The test suite was not
executed while writing this.

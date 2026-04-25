# Participants Matrix

Profile: personal

## Participants
- human-sponsor (human): final-decision, intent-confirmation
- orchestrator-agent (agent): coordination, change-package
- analyst-agent (agent): requirements, scope-analysis
- architect-agent (agent): design, risk-analysis
- executor-agent (agent): implementation, evidence
- verifier-agent (agent): tests, acceptance
- independent-reviewer (agent): review, decision-check
- maintainer-agent (agent): archive, continuity
- hermes-agent (agent): review, decision-check, independent-analysis

## 9-step owner matrix

- Step 1 / Clarify the goal: owner=human-sponsor; assistants=analyst-agent, orchestrator-agent; reviewer=human-sponsor; human_gate=true; final_decision=human-sponsor
- Step 2 / Lock the scope: owner=analyst-agent; assistants=orchestrator-agent; reviewer=human-sponsor; human_gate=true; final_decision=human-sponsor
- Step 3 / Shape the approach: owner=architect-agent; assistants=analyst-agent; reviewer=human-sponsor; human_gate=true; final_decision=human-sponsor
- Step 4 / Assemble the change: owner=orchestrator-agent; assistants=architect-agent; reviewer=human-sponsor; human_gate=false; final_decision=human-sponsor
- Step 5 / Approve the start: owner=human-sponsor; assistants=orchestrator-agent; reviewer=human-sponsor; human_gate=true; final_decision=human-sponsor
- Step 6 / Execute the change: owner=executor-agent; assistants=none; reviewer=verifier-agent; human_gate=false; final_decision=human-sponsor
- Step 7 / Verify the result: owner=verifier-agent; assistants=none; reviewer=independent-reviewer; human_gate=false; final_decision=human-sponsor
- Step 8 / Review and decide: owner=hermes-agent; assistants=human-sponsor; reviewer=hermes-agent; human_gate=true; final_decision=human-sponsor
- Step 9 / Archive and carry forward: owner=maintainer-agent; assistants=orchestrator-agent; reviewer=human-sponsor; human_gate=true; final_decision=human-sponsor

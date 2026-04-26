# Participants Matrix

Profile: personal

## Participants
- human-sponsor (human): sponsor, final-decision
- orchestrator-agent (agent): orchestrator
- analyst-agent (agent): analyst
- architect-agent (agent): architect
- executor-agent (agent): executor
- verifier-agent (agent): verifier
- independent-reviewer (agent): review, decision-check
- maintainer-agent (agent): maintainer
- hermes-agent (agent): reviewer

## 9-step owner matrix

- Step 1 / Clarify the goal: owner=human-sponsor; assistants=orchestrator-agent; reviewer=human-sponsor; human_gate=true; final_decision=human-sponsor
- Step 2 / Lock the scope: owner=analyst-agent; assistants=human-sponsor; reviewer=human-sponsor; human_gate=true; final_decision=human-sponsor
- Step 3 / Shape the approach: owner=architect-agent; assistants=human-sponsor; reviewer=human-sponsor; human_gate=true; final_decision=human-sponsor
- Step 4 / Assemble the change: owner=orchestrator-agent; assistants=architect-agent; reviewer=human-sponsor; human_gate=false; final_decision=human-sponsor
- Step 5 / Approve the start: owner=human-sponsor; assistants=orchestrator-agent; reviewer=human-sponsor; human_gate=true; final_decision=human-sponsor
- Step 6 / Execute the change: owner=executor-agent; assistants=orchestrator-agent; reviewer=verifier-agent; human_gate=false; final_decision=human-sponsor
- Step 7 / Verify the result: owner=verifier-agent; assistants=executor-agent; reviewer=hermes-agent; human_gate=false; final_decision=human-sponsor
- Step 8 / Review and decide: owner=hermes-agent; assistants=human-sponsor; reviewer=hermes-agent; human_gate=true; final_decision=human-sponsor
- Step 9 / Archive and carry forward: owner=maintainer-agent; assistants=human-sponsor; reviewer=human-sponsor; human_gate=true; final_decision=human-sponsor

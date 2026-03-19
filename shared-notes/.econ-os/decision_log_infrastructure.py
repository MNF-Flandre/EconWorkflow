#!/usr/bin/env python3
"""
Econ-OS 2.0 Decision Log Infrastructure
Automated logging, rollback decision, and gate control
"""

import json
import os
from datetime import datetime
from typing import Literal, Dict, Any, Optional
from enum import Enum
from pathlib import Path

# ============ ENUMS ============

class Phase(str, Enum):
    B1 = "B1"  # Explorer
    B2 = "B2"  # Challenger
    C1 = "C1"  # Designer
    C2 = "C2"  # Data Auditor
    D1 = "D1"  # Engineer
    D2 = "D2"  # QA Auditor
    E1 = "E1"  # Runner
    E2 = "E2"  # Adversarial Auditor
    F1 = "F1"  # Narrator
    F2 = "F2"  # Reviewer

class ActionType(str, Enum):
    REJECT_HYPOTHESIS = "REJECT_HYPOTHESIS"
    REQUEST_REVISION = "REQUEST_REVISION"
    AUDIT_RESULT = "AUDIT_RESULT"
    TRIGGER_ROLLBACK = "TRIGGER_ROLLBACK"
    PASS_GATE = "PASS_GATE"
    ESCALATE_TO_USER = "ESCALATE_TO_USER"
    LOCK_SPECIFICATION = "LOCK_SPECIFICATION"

class GateDecision(str, Enum):
    PASS = "PASS"
    PASS_WITH_WARNING = "PASS_WITH_WARNING"
    FAIL = "FAIL"
    ROLLBACK = "ROLLBACK"
    ESCALATE = "ESCALATE"


# ============ DECISION LOG ENTRY ============

class DecisionLogEntry:
    """Single entry to log in decision_log.jsonl"""
    
    def __init__(
        self,
        timestamp: str,
        stage: Phase,
        action: ActionType,
        rationale: str,
        actor: str,
        **kwargs
    ):
        self.timestamp = timestamp or datetime.utcnow().isoformat() + "Z"
        self.stage = stage.value if isinstance(stage, Phase) else stage
        self.action = action.value if isinstance(action, ActionType) else action
        self.rationale = rationale
        self.actor = actor
        self.extra_fields = kwargs
    
    def to_json(self) -> str:
        """Serialize to JSONL format (one line)"""
        entry = {
            "timestamp": self.timestamp,
            "stage": self.stage,
            "action": self.action,
            "rationale": self.rationale,
            "actor": self.actor,
        }
        entry.update(self.extra_fields)
        return json.dumps(entry, ensure_ascii=False)
    
    @staticmethod
    def append_to_file(entry_json: str, log_file_path: Path):
        """Append entry to decision_log.jsonl"""
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_file_path, 'a', encoding='utf-8') as f:
            f.write(entry_json + '\n')


# ============ SCORECARD VALIDATION ============

class ScoreboardGateController:
    """
    Agent A's decision logic - checks scorecard and decides gates
    Does NOT review code quality, only checks metric thresholds
    """
    
    @staticmethod
    def phase_1_gate(hypotheses_file: Path) -> GateDecision:
        """
        Input: hypotheses.yaml
        Check: gap_defined && h_candidates.length > 0 && no duplicates
        """
        import yaml
        try:
            with open(hypotheses_file, 'r') as f:
                h = yaml.safe_load(f)
            
            if h.get('gap_identified') and len(h.get('h_candidates', [])) > 0:
                return GateDecision.PASS
            else:
                return GateDecision.FAIL
        except Exception as e:
            return GateDecision.FAIL
    
    @staticmethod
    def phase_2_gate(design_lock_file: Path) -> GateDecision:
        """
        Input: design_lock.yaml
        Check: c1_design_ready && c2_audit_passed && merge_coverage_expected > 0.85
        """
        import yaml
        try:
            with open(design_lock_file, 'r') as f:
                dl = yaml.safe_load(f)
            
            if (
                dl.get('phase_2_approval_gate', {}).get('c1_design_ready')
                and dl.get('phase_2_approval_gate', {}).get('c2_audit_passed')
            ):
                return GateDecision.PASS
            else:
                return GateDecision.FAIL
        except:
            return GateDecision.FAIL
    
    @staticmethod
    def phase_3_gate(data_scorecard_file: Path) -> tuple[GateDecision, Dict[str, Any]]:
        """
        Input: data_audit_scorecard.json
        Check: merge_coverage >= 0.85
        Return: (decision, metrics)
        """
        try:
            with open(data_scorecard_file, 'r') as f:
                scorecard = json.load(f)
            
            merge_coverage = scorecard.get(
                'rollback_trigger_checks', {}
            ).get('actual_merge_coverage', 0)
            
            sample_loss = 1 - merge_coverage
            
            if merge_coverage >= 0.85:
                decision = GateDecision.PASS
            elif 0.15 < sample_loss <= 0.30:
                decision = GateDecision.PASS_WITH_WARNING
            else:
                decision = GateDecision.ROLLBACK
            
            return decision, {"merge_coverage": merge_coverage}
        except:
            return GateDecision.FAIL, {}
    
    @staticmethod
    def phase_4_gate(regression_scorecard_file: Path) -> tuple[GateDecision, Dict[str, Any]]:
        """
        Input: regression_scorecard.json
        Check: robustness_pass_rate >= 0.5
        """
        try:
            with open(regression_scorecard_file, 'r') as f:
                scorecard = json.load(f)
            
            robustness = scorecard.get(
                'rollback_decision_matrix', {}
            ).get('robustness_pass_rate', 0)
            
            if robustness >= 0.75:
                decision = GateDecision.PASS
            elif 0.50 <= robustness < 0.75:
                decision = GateDecision.PASS_WITH_WARNING
            else:
                decision = GateDecision.ROLLBACK
            
            return decision, {"robustness_pass_rate": robustness}
        except:
            return GateDecision.FAIL, {}


# ============ AUTOMATED ROLLBACK SYSTEM ============

class RollbackEngine:
    """
    Implements rollback_matrix.yaml logic
    Determines which phase to roll back to
    """
    
    ROLLBACK_MAP = {
        # (phase, failure_type) -> (target_phase, action)
        ("B2", "duplicate_research"): ("B1", "Reformulate hypothesis"),
        ("C2", "data_availability_low"): ("C1", "Find proxy variables"),
        ("D2", "sample_loss_critical"): ("C", "Reconsider variable selection"),
        ("E2", "robustness_low"): ("C", "Reconsider identification strategy"),
    }
    
    @staticmethod
    def decide_rollback(
        phase: Phase,
        decision: GateDecision,
        metrics: Dict[str, Any]
    ) -> Optional[tuple[str, str]]:
        """
        Input: Current phase, gate decision, metrics
        Output: (target_phase, action_description)
        
        Returns None if no rollback needed
        """
        if decision == GateDecision.PASS:
            return None
        elif decision == GateDecision.FAIL:
            # Determine failure reason from metrics
            if 'merge_coverage' in metrics and metrics['merge_coverage'] < 0.85:
                return ("C", "Merge coverage below threshold. Reconisder variable definitions.")
            elif 'robustness_pass_rate' in metrics and metrics['robustness_pass_rate'] < 0.5:
                return ("design_lock", "Robustness insufficient. Reconsider identification.")
            else:
                return ("previous_phase", "Critical criterion not met.")
        else:
            return None
    
    @staticmethod
    def log_rollback_decision(
        rollback_target: str,
        reason: str,
        phase: Phase,
        decision_log_file: Path
    ):
        """Log rollback decision to decision_log.jsonl"""
        entry = DecisionLogEntry(
            timestamp=datetime.utcnow().isoformat() + "Z",
            stage=phase,
            action=ActionType.TRIGGER_ROLLBACK,
            rationale=reason,
            actor="Agent_A",
            rollback_target=rollback_target
        )
        DecisionLogEntry.append_to_file(entry.to_json(), decision_log_file)


# ============ EXAMPLE: PHASE 3 GATE CHECK (Auto-invoked by system) ============

def example_phase_3_execution():
    """
    Example: After D2 runs and produces data_audit_scorecard.json,
    this check is automatically called
    """
    project_dir = Path("projects/example-project/.econ-os")
    scorecard_file = project_dir / "phase_3" / "data_audit_scorecard.json"
    decision_log_file = project_dir / "decision_log.jsonl"
    
    # Agent A checks scorecard
    decision, metrics = ScoreboardGateController.phase_3_gate(scorecard_file)
    
    # Decide rollback
    rollback_target = RollbackEngine.decide_rollback(
        Phase.D2,
        decision,
        metrics
    )
    
    if rollback_target:
        # Log and trigger rollback
        RollbackEngine.log_rollback_decision(
            rollback_target=rollback_target[0],
            reason=rollback_target[1],
            phase=Phase.D2,
            decision_log_file=decision_log_file
        )
        print(f"🔄 ROLLBACK TRIGGERED: {rollback_target[0]}")
        return False
    else:
        # Log approval and proceed
        entry = DecisionLogEntry(
            timestamp=datetime.utcnow().isoformat() + "Z",
            stage=Phase.D2,
            action=ActionType.PASS_GATE,
            rationale="Data quality audit passed all thresholds",
            actor="Agent_A",
            merge_coverage=metrics.get('merge_coverage')
        )
        DecisionLogEntry.append_to_file(entry.to_json(), decision_log_file)
        print(f"✅ PHASE 3 PASSED: Proceeding to Phase 4")
        return True


if __name__ == "__main__":
    # Example usage
    example_phase_3_execution()

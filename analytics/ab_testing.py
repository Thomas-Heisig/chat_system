"""
🧪 A/B Testing Framework

Framework for running A/B tests and experiments.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from config.settings import logger


class ExperimentStatus(Enum):
    """Experiment status"""

    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"


class ABTestingFramework:
    """
    A/B testing and experimentation framework.

    Features:
    - Experiment management
    - Variant assignment
    - Metrics collection
    - Statistical analysis
    """

    def __init__(self):
        self.experiments: Dict[str, Dict] = {}
        self.assignments: Dict[str, Dict] = {}

        logger.info("🧪 A/B Testing Framework initialized")

    def create_experiment(
        self,
        name: str,
        variants: List[str],
        description: Optional[str] = None,
        traffic_allocation: Optional[Dict[str, float]] = None,
    ) -> str:
        """
        Create a new experiment.

        Args:
            name: Experiment name
            variants: List of variant names (e.g., ['control', 'variant_a'])
            description: Optional description
            traffic_allocation: Traffic split (e.g., {'control': 0.5, 'variant_a': 0.5})

        Returns:
            Experiment ID
        """
        experiment_id = f"exp_{name.lower().replace(' ', '_')}"

        # Default equal traffic allocation
        if not traffic_allocation:
            allocation = 1.0 / len(variants)
            traffic_allocation = {v: allocation for v in variants}

        experiment = {
            "experiment_id": experiment_id,
            "name": name,
            "description": description or "",
            "variants": variants,
            "traffic_allocation": traffic_allocation,
            "status": ExperimentStatus.DRAFT.value,
            "created_at": datetime.now().isoformat(),
            "metrics": {},
            "assignments": 0,
        }

        self.experiments[experiment_id] = experiment
        logger.info(f"🧪 Experiment created: {name} ({experiment_id})")

        return experiment_id

    def assign_variant(
        self, experiment_id: str, user_id: str, sticky: bool = True
    ) -> Optional[str]:
        """
        Assign user to experiment variant.

        Args:
            experiment_id: Experiment ID
            user_id: User identifier
            sticky: Keep same assignment for user (default: True)

        Returns:
            Assigned variant or None
        """
        if experiment_id not in self.experiments:
            return None

        experiment = self.experiments[experiment_id]

        # Check if already assigned (sticky)
        assignment_key = f"{experiment_id}:{user_id}"
        if sticky and assignment_key in self.assignments:
            return self.assignments[assignment_key]["variant"]

        # Assign based on traffic allocation (deterministic based on user_id)
        variants = experiment["variants"]
        allocation = experiment["traffic_allocation"]

        # Use hash for deterministic assignment
        import hashlib

        hash_input = f"{experiment_id}:{user_id}".encode()
        hash_value = int(hashlib.md5(hash_input).hexdigest(), 16)
        rand = (hash_value % 10000) / 10000.0  # Normalize to 0-1

        cumulative = 0.0
        assigned_variant = variants[0]  # fallback

        for variant in variants:
            cumulative += allocation.get(variant, 0)
            if rand <= cumulative:
                assigned_variant = variant
                break

        # Store assignment
        self.assignments[assignment_key] = {
            "experiment_id": experiment_id,
            "user_id": user_id,
            "variant": assigned_variant,
            "assigned_at": datetime.now().isoformat(),
        }

        experiment["assignments"] += 1

        return assigned_variant

    def track_metric(self, experiment_id: str, user_id: str, metric_name: str, value: float):
        """
        Track metric for experiment.

        Args:
            experiment_id: Experiment ID
            user_id: User identifier
            metric_name: Metric name
            value: Metric value
        """
        if experiment_id not in self.experiments:
            return

        assignment_key = f"{experiment_id}:{user_id}"
        if assignment_key not in self.assignments:
            return

        variant = self.assignments[assignment_key]["variant"]
        experiment = self.experiments[experiment_id]

        if metric_name not in experiment["metrics"]:
            experiment["metrics"][metric_name] = {}

        if variant not in experiment["metrics"][metric_name]:
            experiment["metrics"][metric_name][variant] = []

        experiment["metrics"][metric_name][variant].append(
            {"user_id": user_id, "value": value, "timestamp": datetime.now().isoformat()}
        )

    def get_experiment_results(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        """
        Get experiment results.

        Args:
            experiment_id: Experiment ID

        Returns:
            Results summary
        """
        if experiment_id not in self.experiments:
            return None

        experiment = self.experiments[experiment_id]

        # Calculate metrics summary
        metrics_summary = {}
        for metric_name, variant_data in experiment["metrics"].items():
            metrics_summary[metric_name] = {}

            for variant, values in variant_data.items():
                if values:
                    metric_values = [v["value"] for v in values]
                    metrics_summary[metric_name][variant] = {
                        "count": len(metric_values),
                        "mean": sum(metric_values) / len(metric_values),
                        "min": min(metric_values),
                        "max": max(metric_values),
                    }

        return {
            "experiment_id": experiment_id,
            "name": experiment["name"],
            "status": experiment["status"],
            "total_assignments": experiment["assignments"],
            "metrics": metrics_summary,
        }

    def start_experiment(self, experiment_id: str) -> bool:
        """Start experiment"""
        if experiment_id in self.experiments:
            self.experiments[experiment_id]["status"] = ExperimentStatus.ACTIVE.value
            return True
        return False

    def stop_experiment(self, experiment_id: str) -> bool:
        """Stop experiment"""
        if experiment_id in self.experiments:
            self.experiments[experiment_id]["status"] = ExperimentStatus.COMPLETED.value
            return True
        return False


# Singleton instance
_ab_testing: Optional[ABTestingFramework] = None


def get_ab_testing() -> ABTestingFramework:
    """Get or create A/B testing framework singleton"""
    global _ab_testing
    if _ab_testing is None:
        _ab_testing = ABTestingFramework()
    return _ab_testing

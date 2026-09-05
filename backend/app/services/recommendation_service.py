"""
RecommendationService — placeholder for future AI agent integration.

FUTURE AI AGENT INTEGRATION:
─────────────────────────────────────────────────────────────────────────
Replace DemoRecommendationService with AIRecommendationService.
The AIRecommendationService should:
1. Call the Python AI agent (Ollama or other LLM).
2. Pass employee analytics context.
3. Return structured RecommendationResult objects.

The route handler and frontend do NOT need to change.
─────────────────────────────────────────────────────────────────────────
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any


class RecommendationService(ABC):
    @abstractmethod
    def get_recommendations(self, employee_id: str, context: Dict[str, Any]) -> List[Dict]:
        pass


class DemoRecommendationService(RecommendationService):
    """
    Demo implementation with deterministic rule-based recommendations.
    Source: DEMO_RULE (not AI).
    Replace with AIRecommendationService for LLM-based insights.
    """

    def get_recommendations(self, employee_id: str, context: Dict[str, Any]) -> List[Dict]:
        recommendations = []
        metrics = context.get("metrics", {})
        attendance_rate = metrics.get("attendance_rate", 100)
        overtime_hours = metrics.get("total_overtime_hours", 0)
        late_count = metrics.get("late_count", 0)
        leave_used = metrics.get("leave_used", 0)
        leave_remaining = metrics.get("leave_remaining", 0)

        # Rule: High overtime → workload concern
        if overtime_hours > 20:
            recommendations.append({
                "type": "WORKLOAD_CONCERN",
                "title": "High Overtime Hours",
                "description": f"Employee has logged {overtime_hours:.1f} overtime hours this period. Consider reviewing workload distribution.",
                "priority": "HIGH",
                "source": "DEMO_RULE",
                "demo_label": "Demo Recommendation",
            })

        # Rule: Good attendance → recognition
        if attendance_rate >= 98:
            recommendations.append({
                "type": "PERFORMANCE_RECOGNITION",
                "title": "Excellent Attendance Record",
                "description": f"Attendance rate of {attendance_rate:.1f}% is outstanding. Consider recognition or positive feedback.",
                "priority": "MEDIUM",
                "source": "DEMO_RULE",
                "demo_label": "Demo Recommendation",
            })

        # Rule: Multiple late arrivals
        if late_count >= 3:
            recommendations.append({
                "type": "ATTENDANCE_IMPROVEMENT",
                "title": "Recurring Late Arrivals",
                "description": f"Employee has been late {late_count} times this period. A conversation about punctuality may be beneficial.",
                "priority": "MEDIUM",
                "source": "DEMO_RULE",
                "demo_label": "Demo Recommendation",
            })

        # Rule: Low attendance → concern
        if attendance_rate < 80:
            recommendations.append({
                "type": "ATTENDANCE_CONCERN",
                "title": "Below Average Attendance",
                "description": f"Attendance rate of {attendance_rate:.1f}% is below the expected 85% threshold. Please investigate.",
                "priority": "HIGH",
                "source": "DEMO_RULE",
                "demo_label": "Demo Recommendation",
            })

        # Rule: Leave not utilized
        if leave_remaining > 15:
            recommendations.append({
                "type": "LEAVE_UTILIZATION",
                "title": "Unused Annual Leave",
                "description": f"Employee has {leave_remaining} days of unused annual leave. Encourage them to plan time off to prevent burnout.",
                "priority": "LOW",
                "source": "DEMO_RULE",
                "demo_label": "Demo Recommendation",
            })

        # Rule: Strong performance with overtime → increment consideration
        if attendance_rate >= 95 and overtime_hours >= 10:
            recommendations.append({
                "type": "INCREMENT_CONSIDERATION",
                "title": "Eligible for Increment Review",
                "description": "Strong performance indicators with high attendance and significant overtime contribution. Consider for increment review cycle.",
                "priority": "HIGH",
                "source": "DEMO_RULE",
                "demo_label": "Demo Recommendation — Awaiting AI Analysis",
            })

        if not recommendations:
            recommendations.append({
                "type": "NO_CONCERNS",
                "title": "Performance on Track",
                "description": "No specific recommendations at this time. Employee performance metrics are within expected range.",
                "priority": "LOW",
                "source": "DEMO_RULE",
                "demo_label": "Demo Recommendation",
            })

        return recommendations


# TODO: Replace with AIRecommendationService when AI agent is integrated
recommendation_service: RecommendationService = DemoRecommendationService()

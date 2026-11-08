import json
import operator
from typing import Any, Dict, List, Tuple
import streamlit as st

OPS = {
    "==": operator.eq,
    "!=": operator.ne,
    ">": operator.gt,
    ">=": operator.ge,
    "<": operator.lt,
    "<=": operator.le,
    "in": lambda a, b: a in b,
    "not_in": lambda a, b: a not in b,
}

DEFAULT_RULES: List[Dict[str, Any]] = [
    {
        "name": "Top merit candidate",
        "priority": 100,
        "conditions": [
            ["cgpa", ">=", 3.7],
            ["co_curricular_score", ">=", 80],
            ["family_income", "<=", 8000],
            ["disciplinary_actions", "==", 0],
        ],
        "action": {
            "decision": "AWARD_FULL",
            "reason": "Excellent academic & co-curricular performance, with acceptable need",
        },
    },
    {
        "name": "Good candidate - partial scholarship",
        "priority": 80,
        "conditions": [
            ["cgpa", ">=", 3.3],
            ["co_curricular_score", ">=", 60],
            ["family_income", "<=", 12000],
            ["disciplinary_actions", "<=", 1],
        ],
        "action": {
            "decision": "AWARD_PARTIAL",
            "reason": "Good academic & involvement record with moderate need",
        },
    },
    {
        "name": "Need-based review",
        "priority": 70,
        "conditions": [
            ["cgpa", ">=", 2.5],
            ["family_income", "<=", 4000],
        ],
        "action": {
            "decision": "REVIEW",
            "reason": "High need but borderline academic score",
        },
    },
    {
        "name": "Low CGPA – not eligible",
        "priority": 95,
        "conditions": [["cgpa", "<", 2.5]],
        "action": {
            "decision": "REJECT",
            "reason": "CGPA below minimum scholarship requirement",
        },
    },
    {
        "name": "Serious disciplinary record",
        "priority": 90,
        "conditions": [["disciplinary_actions", ">=", 2]],
        "action": {
            "decision": "REJECT",
            "reason": "Too many disciplinary records",
        },
    },
]

FACT_FIELDS = {
    "cgpa", "family_income", "co_curricular_score",
    "community_service_hours", "semester", "disciplinary_actions",
}


def evaluate_condition(facts: Dict[str, Any], cond: List[Any]) -> bool:
    """Check one condition against applicant facts."""
    if not isinstance(cond, list) or len(cond) != 3:
        return False
    field, op, value = cond
    if not isinstance(field, str) or not isinstance(op, str):
        return False
    if field not in facts or op not in OPS:
        return False
    try:
        return bool(OPS[op](facts[field], value))
    except (TypeError, ValueError):
        return False


def rule_matches(facts: Dict[str, Any], rule: Dict[str, Any]) -> bool:
    """A rule fires when all its conditions are true."""
    return all(evaluate_condition(facts, c) for c in rule["conditions"])


def run_rules(
    facts: Dict[str, Any], rules: List[Dict[str, Any]]
) -> Tuple[Dict[str, str], List[Dict[str, Any]]]:
    """Return highest-priority matching action and all matching rules."""
    fired = [rule for rule in rules if rule_matches(facts, rule)]
    fired.sort(key=lambda rule: rule["priority"], reverse=True)
    if not fired:
        return {"decision": "REVIEW", "reason": "No rule matched; committee review required"}, []
    return fired[0]["action"], fired


def validate_rules(rules: Any) -> None:
    """Reject malformed rules instead of silently changing the rule set."""
    if not isinstance(rules, list) or not rules:
        raise ValueError("Rules must be a non-empty JSON array.")
    for i, rule in enumerate(rules, start=1):
        if not isinstance(rule, dict):
            raise ValueError(f"Rule {i} must be an object.")
        if not isinstance(rule.get("name"), str) or not rule["name"].strip():
            raise ValueError(f"Rule {i} needs a name.")
        if type(rule.get("priority")) is not int:
            raise ValueError(f"Rule {i} priority must be an integer.")
        conditions = rule.get("conditions")
        if not isinstance(conditions, list) or not conditions:
            raise ValueError(f"Rule {i} needs at least one condition.")
        for condition in conditions:
            if not isinstance(condition, list) or len(condition) != 3:
                raise ValueError(f"Rule {i} has an invalid condition format.")
            field, op, value = condition
            if field not in FACT_FIELDS or op not in OPS:
                raise ValueError(f"Rule {i} has an unknown field or operator.")
            if op in ("in", "not_in"):
                if not isinstance(value, (list, str)):
                    raise ValueError(f"Rule {i}: membership requires a list or string.")
            elif not isinstance(value, (int, float)) or isinstance(value, bool):
                raise ValueError(f"Rule {i}: comparison value must be numeric.")
        action = rule.get("action")
        if not isinstance(action, dict) or action.get("decision") not in {
            "AWARD_FULL", "AWARD_PARTIAL", "REVIEW", "REJECT"
        } or not isinstance(action.get("reason"), str):
            raise ValueError(f"Rule {i} has an invalid action.")


def main() -> None:
    st.set_page_config(page_title="Scholarship Advisory System", page_icon="🎓", layout="wide")
    st.title("🎓 Scholarship Advisory Rule-Based System")
    st.caption("BSD3513 • Lab Report 3 | Transparent scholarship eligibility advice")
    st.info("This is a decision-support prototype. Final scholarship awards require committee approval.")

    with st.sidebar:
        st.header("Applicant Facts")
        cgpa = st.number_input("CGPA", min_value=0.0, max_value=4.0, value=3.5, step=0.01, format="%.2f")
        family_income = st.number_input("Monthly family income (RM)", min_value=0, value=5000, step=100)
        co_curricular_score = st.number_input("Co-curricular score (0–100)", min_value=0, max_value=100, value=70)
        community_service_hours = st.number_input("Community service hours", min_value=0, value=20)
        semester = st.number_input("Current semester", min_value=1, max_value=30, value=3)
        disciplinary_actions = st.number_input("Disciplinary actions", min_value=0, value=0)
        st.divider()
        st.header("Rules (JSON)")
        st.caption("Edit the rules to test other configurations. Defaults match the lab handout.")
        rules_text = st.text_area("JSON rule editor", value=json.dumps(DEFAULT_RULES, indent=2, ensure_ascii=False), height=280)
        evaluate = st.button("Evaluate Scholarship", type="primary", use_container_width=True)

    facts = {
        "cgpa": float(cgpa),
        "family_income": int(family_income),
        "co_curricular_score": int(co_curricular_score),
        "community_service_hours": int(community_service_hours),
        "semester": int(semester),
        "disciplinary_actions": int(disciplinary_actions),
    }
    left, right = st.columns(2)
    with left:
        st.subheader("Applicant Facts")
        st.json(facts)
    rules = None
    try:
        rules = json.loads(rules_text)
        validate_rules(rules)
    except (json.JSONDecodeError, ValueError, TypeError) as exc:
        st.error(f"Rule configuration error: {exc}. Correct the JSON before evaluating.")
    with right:
        st.subheader("Active Rules")
        if rules is not None:
            st.write(f"{len(rules)} configured rules")
            with st.expander("View active JSON rules"):
                st.code(json.dumps(rules, indent=2, ensure_ascii=False), language="json")

    st.divider()
    if evaluate:
        if rules is None:
            st.warning("Evaluation skipped because the rule configuration is invalid.")
            return
        action, fired = run_rules(facts, rules)
        decision, reason = action["decision"], action["reason"]
        st.subheader("Scholarship Recommendation")
        if decision == "AWARD_FULL":
            st.success(f"FULL SCHOLARSHIP (AWARD_FULL) — {reason}")
        elif decision == "AWARD_PARTIAL":
            st.success(f"PARTIAL SCHOLARSHIP (AWARD_PARTIAL) — {reason}")
        elif decision == "REJECT":
            st.error(f"NOT ELIGIBLE (REJECT) — {reason}")
        else:
            st.warning(f"MANUAL REVIEW (REVIEW) — {reason}")
        st.subheader("Matched Rules (highest priority first)")
        if not fired:
            st.info("No rules matched. The case has been referred for review.")
        for index, rule in enumerate(fired, start=1):
            with st.expander(f"{index}. {rule['name']} | Priority {rule['priority']}", expanded=index == 1):
                st.write(f"**Decision:** {rule['action']['decision']}")
                st.write(f"**Reason:** {rule['action']['reason']}")
                for condition in rule["conditions"]:
                    st.code(str(condition))
        st.caption("Note: community service hours and semester are collected as required, but are not referenced by the five default lab rules.")
    else:
        st.info("Enter applicant details, optionally edit the JSON rules, then click Evaluate Scholarship.")


if __name__ == "__main__":
    main()

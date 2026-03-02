import json
import argparse
import re
import sys

def check_security(checkov_data, policies):
    critical = []
    high = []
    medium = []
    
    critical_ids = policies["security"]["critical_blocking"]
    high_ids = policies["security"]["high_blocking"]
    medium_ids = policies["security"]["medium_non_blocking"]
    
    results = checkov_data if isinstance(checkov_data, list) else [checkov_data]
    
    for result in results:
        failed_checks = []
        if isinstance(result, dict):
            if "results" in result:
                failed_checks = result["results"].get("failed_checks", [])
            elif "failed_checks" in result:
                failed_checks = result["failed_checks"]
        
        for check in failed_checks:
            check_id = check.get("check_id", "")
            check_type = check.get("check_type", "terraform")
            resource = check.get("resource", "unknown")
            
            if check_id in critical_ids:
                critical.append({"id": check_id, "resource": resource, "type": check_type})
            elif check_id in high_ids:
                high.append({"id": check_id, "resource": resource, "type": check_type})
            elif check_id in medium_ids:
                medium.append({"id": check_id, "resource": resource, "type": check_type})
    
    blocking = len(critical) > 0 or len(high) > 0
    return {"critical": critical, "high": high, "medium": medium, "blocking": blocking}

def check_cost(infracost_data, policies):
    cost_policies = policies["cost"]
    
    total_monthly_cost = 0
    prev_monthly_cost = 0
    resources = []
    
    projects = infracost_data.get("projects", [])
    for project in projects:
        breakdown = project.get("breakdown", {})
        resources.extend(breakdown.get("resources", []))
        total_monthly_cost += float(breakdown.get("totalMonthlyCost", 0) or 0)
        prev_monthly_cost += float(project.get("pastBreakdown", {}).get("totalMonthlyCost", 0) or 0)
    
    delta = total_monthly_cost - prev_monthly_cost
    percent_increase = ((delta / prev_monthly_cost) * 100) if prev_monthly_cost > 0 else 0
    
    status = "PASS"
    issues = []
    
    if delta > cost_policies["monthly_spike_fail_threshold"]:
        status = "FAIL"
        issues.append(f"Cost increase ${delta:.2f}/month exceeds critical threshold ${cost_policies['monthly_spike_fail_threshold']}")
    elif delta > cost_policies["monthly_spike_warn_threshold"]:
        status = "WARN"
        issues.append(f"Cost increase ${delta:.2f}/month exceeds warning threshold ${cost_policies['monthly_spike_warn_threshold']}")
    
    if percent_increase > cost_policies["max_increase_percent"]:
        status = "FAIL"
        issues.append(f"Cost increase {percent_increase:.1f}% exceeds max allowed {cost_policies['max_increase_percent']}%")
    
    top_resources = sorted(resources, key=lambda x: float(x.get("monthlyCost", 0) or 0), reverse=True)[:5]
    
    return {
        "status": status,
        "total_monthly_cost": total_monthly_cost,
        "prev_monthly_cost": prev_monthly_cost,
        "delta": delta,
        "percent_increase": percent_increase,
        "issues": issues,
        "top_resources": top_resources,
        "blocking": status == "FAIL"
    }

def check_compliance(checkov_data, policies):
    compliance_policies = policies["compliance"]
    issues = []
    
    results = checkov_data if isinstance(checkov_data, list) else [checkov_data]
    for result in results:
        failed_checks = []
        if isinstance(result, dict):
            if "results" in result:
                failed_checks = result["results"].get("failed_checks", [])
        
        for check in failed_checks:
            resource = check.get("resource", "")
            for blocked in compliance_policies["blocked_services"]:
                if blocked in resource:
                    issues.append(f"Blocked service used: {resource}")
    
    return {"issues": issues, "blocking": len(issues) > 0}

def generate_report(security, cost, compliance):
    overall = "✅ PASS"
    if security["blocking"] or cost["blocking"] or compliance["blocking"]:
        overall = "❌ FAIL"
    elif cost["status"] == "WARN":
        overall = "⚠️ WARN"
    
    report = f"""## 🏛️ Terraform PR Governance Report

### Overall Status: {overall}

---

### 🔒 Security Analysis

| Severity | Count | Blocking |
|----------|-------|----------|
| 🔴 Critical | {len(security['critical'])} | Yes |
| 🟠 High | {len(security['high'])} | Yes |
| 🟡 Medium | {len(security['medium'])} | No |

"""
    if security["critical"]:
        report += "**Critical Violations:**\n"
        for v in security["critical"]:
            report += f"- `{v['id']}` on `{v['resource']}`\n"
        report += "\n"
    
    if security["high"]:
        report += "**High Violations:**\n"
        for v in security["high"]:
            report += f"- `{v['id']}` on `{v['resource']}`\n"
        report += "\n"

    report += f"""---

### 💰 Cost Analysis

| Metric | Value |
|--------|-------|
| Previous Monthly Cost | ${cost['prev_monthly_cost']:.2f} |
| New Monthly Cost | ${cost['total_monthly_cost']:.2f} |
| Delta | ${cost['delta']:+.2f} |
| % Change | {cost['percent_increase']:+.1f}% |
| Status | {cost['status']} |

"""
    if cost["issues"]:
        report += "**Cost Issues:**\n"
        for issue in cost["issues"]:
            report += f"- {issue}\n"
        report += "\n"

    report += "---\n\n### ✅ Compliance\n\n"
    if compliance["issues"]:
        report += "**Compliance Issues:**\n"
        for issue in compliance["issues"]:
            report += f"- {issue}\n"
    else:
        report += "No compliance issues found.\n"

    return report

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkov", required=True)
    parser.add_argument("--infracost", required=True)
    parser.add_argument("--policies", required=True)
    args = parser.parse_args()
    
    with open(args.checkov) as f:
        checkov_data = json.load(f)
    with open(args.infracost) as f:
        infracost_data = json.load(f)
    with open(args.policies) as f:
        policies = json.load(f)
    
    security = check_security(checkov_data, policies)
    cost = check_cost(infracost_data, policies)
    compliance = check_compliance(checkov_data, policies)
    
    report = generate_report(security, cost, compliance)
    print(report)
    
    if security["blocking"] or cost["blocking"] or compliance["blocking"]:
        sys.exit(1)

if __name__ == "__main__":
    main()
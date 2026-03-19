# Agentic DevOps AutoFix on Kubernetes (Human-in-the-Loop)

A **production-style sample project** that demonstrates how an **AI-powered DevOps remediation agent** can detect Kubernetes incidents, recommend safe fixes, request **human approval**, apply the remediation, and verify rollout.

This project is designed as a **portfolio-grade DevOps / Platform Engineering / MLOps demo** and showcases:

- **Kubernetes incident detection**
- **Policy-based safe remediation**
- **Human-in-the-loop approval workflow**
- **Automated remediation execution**
- **Audit logging for traceability**
- **Rollout verification**
- **Safer operational design for real-world production systems**

---

# 🚀 Why This Project?

Modern DevOps teams want:

- faster incident response
- reduced MTTR (Mean Time To Recovery)
- safe automation
- better reliability
- less manual toil

But **fully autonomous remediation is risky**.

In production, an AI/automation system should **not blindly modify infrastructure** without:

- policy checks
- audit trail
- approval gates for risky actions
- rollback awareness
- blast radius control

This project demonstrates the **right balance**:

> **AI suggests + Human approves + System executes safely**

This is the practical model for **Agentic DevOps** and **AIOps** in real production environments.

---

# 🧠 Problem This Demo Solves

A sample Kubernetes application (`fragile-app`) intentionally crashes because it is missing an environment variable:

- `STRIPE_API_KEY`

The agent detects:

- Pod is in `CrashLoopBackOff`

It analyzes logs, infers root cause, and recommends:

- inject missing env var into the Deployment

Then it:

1. creates an approval request
2. waits for human approval
3. applies the fix
4. waits for rollout
5. verifies the deployment update
6. records audit logs

---

# 🏗️ Architecture

```text
Kubernetes Cluster (kind / local)
        |
        v
+-------------------------+
|   fragile-app Pod       |
| CrashLoopBackOff        |
+-------------------------+
        |
        v
+-------------------------+
| observer.py             |
| Detects incident        |
| Reads logs/status       |
+-------------------------+
        |
        v
+-------------------------+
| policy.py               |
| Validates safe actions  |
+-------------------------+
        |
        v
+-------------------------+
| approval.py             |
| Creates approval file   |
| Waits for human input   |
+-------------------------+
        |
        v
+-------------------------+
| executor.py             |
| Applies safe fix        |
| Verifies rollout        |
+-------------------------+
        |
        v
+-------------------------+
| audit.py                |
| Writes audit records    |
+-------------------------+

### Project Structure

agentic-devops-autofix/
│
├── agent/
│   ├── __init__.py
│   ├── main.py
│   ├── observer.py
│   ├── approval.py
│   ├── executor.py
│   ├── policy.py
│   └── audit.py
│
├── k8s/
│   ├── namespace.yaml
│   └── fragile-app.yaml
│
├── scripts/
│   ├── approve_fix.sh
│   └── approve_fix.ps1
│
├── approvals/          # auto-created at runtime
├── audits/             # auto-created at runtime
├── state/              # auto-created at runtime
│
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md

⚙️ Core Components
1. observer.py

Responsible for:

polling Kubernetes pods
detecting CrashLoopBackOff
analyzing pod logs
generating remediation recommendations
preventing duplicate incidents using state tracking

Why it exists

Without an observer, the system cannot understand cluster health or convert raw failures into actionable incidents.

2. policy.py

Responsible for:

deciding whether a recommended action is safe
allowing only low-risk, pre-approved actions
blocking dangerous or untrusted actions

Why it exists

Automation without policy is dangerous.

Example:

safe: inject a known missing env var

unsafe: delete deployment, scale to zero, restart critical workloads blindly

3. approval.py

Responsible for:

creating approval requests
waiting for human approval
enforcing timeout
Why human interaction is needed
Even if AI is correct, production systems require:
accountability
compliance
change control
risk review
operational awareness

### Human approval reduces blast radius and ensures:

safe governance
auditability
production confidence

This is especially important for:

payment systems
customer-facing APIs
regulated environments
production databases
critical infrastructure

4. executor.py

Responsible for:

mapping pod -> ReplicaSet -> Deployment

applying safe fixes
triggering rollout
verifying rollout success
Why this approach is used

For env injection, we use:

kubectl set env deployment/<name> KEY=VALUE

instead of raw JSON patch because:

safer on Windows
simpler than merge patch
triggers proper rollout
less error-prone

more production-friendly

5. audit.py

Responsible for:

writing audit records
storing incident ID
storing recommendation
storing policy decision
storing execution result
Why audit logging matters
Every automated action should be traceable.

Audit logs help with:

compliance
postmortems
incident review
debugging
security investigations

🔐 Why Human-in-the-Loop Is Important

This project intentionally uses Human-in-the-Loop (HITL) instead of full autonomy.

Benefits of HITL
1. Reduces risk

Even a correct AI recommendation can be unsafe in the wrong environment.

2. Supports governance

Many teams require:

change approval

operational ownership

documented action trail

3. Prevents catastrophic automation

Imagine an AI incorrectly deciding to:

delete pods repeatedly

scale down a production service

overwrite secrets

restart critical workloads during peak traffic

4. Builds trust

Teams adopt automation faster when they can:

inspect recommendation

approve only safe actions

retain control

🛡️ Security Best Practices Used

This project demonstrates several real-world best practices:

1. Policy-based allowlist

Only explicitly approved actions should be executed.

Example safe actions:

inject_env
increase_probe_delay
increase_memory (if bounded)

Example blocked actions:

delete deployment
scale critical service to zero
rollback without release metadata
secret mutation without governance

2. No hardcoded real secrets

The demo uses a fake test value:

sk_test_demo_123

In real production:

never hardcode secrets in code

use:

Kubernetes Secrets
External Secrets Operator
AWS Secrets Manager
HashiCorp Vault
SOPS / Sealed Secrets

3. Human approval for changes

All infrastructure changes should be:

visible
approved
logged

4. Audit every action

Every incident should record:

what was detected
why the action was recommended
whether policy allowed it
whether approval was granted
what command was executed
whether rollout succeeded
Minimize blast radius

The agent:

only acts on known failure patterns
only executes pre-approved low-risk fixes
avoids broad cluster-wide mutation


🛠️ How to Run
1. Clone repository
git clone <your-repo-url>
cd agentic-devops-autofix
2. Create virtual environment
Windows PowerShell
python -m venv .venv
.venv\Scripts\Activate.ps1
Linux / Git Bash
python -m venv .venv
source .venv/bin/activate
3. Install dependencies
pip install -r requirements.txt
4. Create kind cluster (example)
kind create cluster --name autofix-demo
5. Deploy Kubernetes resources
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/fragile-app.yaml
6. Run the agent
python -m agent.main
7. Approve the fix
Windows PowerShell
.\scripts\approve_fix.ps1 incident-<ID>
Git Bash / Linux
./scripts/approve_fix.sh incident-<ID>
8. Watch pod recovery
kubectl get pods -n autofix-demo -w

You should see:

old pod terminating

new pod created

new pod becoming Running
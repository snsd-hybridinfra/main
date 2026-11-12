
# Target Portability Architecture

## Adapter Model

```mermaid
flowchart TD
  Profile["Environment profile"] --> Type{"Target type"}
  Type -->|"OpenStack VM"| OSAdapter["OpenStack provision adapter"]
  Type -->|"Existing VM"| VMAdapter["Existing target registration"]
  Type -->|"Physical server"| HWAdapter["Physical target registration"]
  OSAdapter --> Contract["Common host-onboarding contract"]
  VMAdapter --> Contract
  HWAdapter --> Contract
  Contract --> Inventory["Common generated inventory"]
  Inventory --> CaC["Target-independent Configuration as Code"]
```

OpenStack may provision compute. Existing VM and physical-server adapters never claim creation. The user performs hardware, base OS, console, interface, storage, and initial-access prerequisites; Codex-managed validation and automation begin after access is approved.

Future AWS, Azure, Kubernetes, and additional OpenStack adapters implement the same profile, plan, inventory, approval, onboarding, and evidence contracts. Their status is `ROADMAP_ONLY`.

Profiles live under `profiles/templates/` and contain placeholders only. They exclude passwords, tokens, keys, client secrets, MFA material, private cloud configuration, and real environment dumps.

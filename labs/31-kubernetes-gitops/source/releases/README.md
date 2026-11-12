# IDP container release desired state

This directory is the GitOps promotion authority for the seven central-IDP
images. The checked-in baseline is intentionally empty. The protected container
supply-chain workflow writes one immutable release directory and changes this
root `kustomization.yaml` on a dedicated `codex/release-*` branch.

Only a reviewed merge to `main` authorizes Argo CD reconciliation. Raw scanner
reports, credentials, signing material and kubeconfig are never written here.
Rollback is a reviewed Git revert or a new promotion which points this root to a
previous accepted immutable release.

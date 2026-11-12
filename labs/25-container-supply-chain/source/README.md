# IDP container supply-chain runtime

This directory owns the reviewed container build, verification and GitOps
promotion machinery. It does not authorize a registry publish or a k3s change.

## Dedicated runner bundle

`tools/local-vm/New-IdpSupplyChainRunnerVm.ps1` creates the bounded VMware
runner. Its external manifest must validate against
`schemas/idp-runner-bundle-manifest.schema.json`. Keep the manifest, bundle,
private dispatch key and all raw installation output outside Git.

The private GitHub Release is the reviewed distribution authority. Bootstrap
does not place a GitHub token in cloud-init: the provisioner verifies the same
local asset digest, creates a read-only ISO containing only the bundle and
manifest, and attaches that ISO to the VM.

The single reviewed bundle must contain an `install.sh` at its root. That
installer owns the Docker daemon, grants only `idprunner` access to its socket,
and installs the exact files declared by the manifest.
It must also install these root-owned commands:

- `/usr/local/sbin/idp-egress-policy-apply`
- `/usr/local/sbin/idp-egress-policy-check`

The policy must deny default egress and allow only the GitHub Actions control
plane, reviewed source fetches, the approved private registry, Sigstore and the
approved vulnerability database. The reviewed source-fetch class is limited to
PyPI metadata and wheel delivery; the vulnerability-database class includes the
Trivy mirror and its GHCR fallback. Squid accepts proxy clients only from the
host loopback, the Docker bridge and the dedicated BuildKit bridge. It must deny
Kubernetes API egress. The
provisioner verifies every declared executable, Docker daemon health, Buildx,
the strict egress check and kubeconfig absence before writing its local ready
marker.

Provisioning uses the reviewed Ubuntu VMDK and a dedicated ED25519 public key:

```powershell
tools/local-vm/New-IdpSupplyChainRunnerVm.ps1 `
  -ImagePath <reviewed-ubuntu-vmdk> `
  -VmDirectory <new-empty-vm-directory> `
  -DispatchPublicKeyPath <dedicated-public-key> `
  -RunnerBundleManifestPath <reviewed-external-manifest> `
  -RunnerBundlePath <matching-reviewed-bundle> `
  -Start
```

The SSH key is forced to `idp-runner-dispatch`; it cannot request a shell,
forward an agent or run an arbitrary remote command. A fresh GitHub JIT configuration is
sent only on standard input. The GitHub registration is ephemeral and accepts
one job; the workspace is deleted after that job. Never store a registration
token or JIT configuration in Git, the VMX, the manifest or evidence.

The same forced key accepts only the exact `proxy-denials` diagnostic command.
It emits the client address, Squid decision, HTTP method and CONNECT target for
recent denied requests to the local operator; it does not emit URL paths,
headers, credentials or response bodies. All other remote commands remain
denied.

The VM JSON response deliberately reports `runtime_validated: false`. Promote
runtime readiness only after independent GitHub runner, tool digest, egress,
one-job removal and clean-workspace evidence has been sanitized and reviewed.

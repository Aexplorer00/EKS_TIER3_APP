# 🔥 Kubernetes Chaos Engineering Lab

> **Purpose:** Intentionally break things in your K8s cluster, practice debugging, and build muscle memory for the most-asked SRE interview questions.
>
> **Prerequisites:** Your EKS-3Tier-App deployed and running on a cluster (Minikube or online playground like KillerCoda).

---

## 🎯 Lab Overview

| Lab # | Scenario | Maps to Interview Question |
|-------|----------|---------------------------|
| 1 | CrashLoopBackOff | "Pod is in CrashLoopBackOff — what do you do?" |
| 2 | ImagePullBackOff | "ImagePullBackOff — how do you fix it?" |
| 3 | Pod Stuck in Pending | "Pod stuck in Pending — what could be wrong?" |
| 4 | OOMKilled | "Pod keeps getting OOMKilled — what do you do?" |
| 5 | Service Not Routing Traffic | "Service not routing traffic — debugging steps?" |
| 6 | DNS Resolution Failure | "How do you debug DNS issues inside a cluster?" |
| 7 | Liveness Probe Failure | "Pod keeps restarting — what's happening?" |
| 8 | Resource Quota Exhaustion | "Deployment won't scale — why?" |

---

## ⚙️ Setup

```bash
# Create the chaos namespace
kubectl apply -f chaos-lab/00-namespace.yaml

# Deploy a healthy baseline app first
kubectl apply -f chaos-lab/00-healthy-baseline.yaml

# Verify everything is running
kubectl get pods -n chaos-lab
# Expected: All pods Running, 1/1 Ready
```

---

## Lab 1: CrashLoopBackOff — Bad Command

### 🔴 Break It
```bash
kubectl apply -f chaos-lab/01-crashloop-bad-command.yaml
```

### What Happens
The pod has a bad startup command that exits immediately. Kubernetes keeps restarting it → CrashLoopBackOff.

### 🔍 Debug It (Practice These Commands)
```bash
# Step 1: Check pod status
kubectl get pods -n chaos-lab
# You'll see: STATUS = CrashLoopBackOff, RESTARTS increasing

# Step 2: Check events
kubectl describe pod -l chaos=crashloop-cmd -n chaos-lab
# Look at Events section → "Back-off restarting failed container"

# Step 3: Check logs — THIS IS KEY
kubectl logs -l chaos=crashloop-cmd -n chaos-lab
# You'll see: error from the bad command

# Step 4: Check the container exit code
kubectl get pod -l chaos=crashloop-cmd -n chaos-lab -o jsonpath='{.items[0].status.containerStatuses[0].lastState.terminated.exitCode}'
# Exit code 1 = application error, 137 = OOMKilled, 139 = segfault
```

### ✅ Fix It
```bash
# The command is wrong — fix by deploying the correct version
kubectl apply -f chaos-lab/01-crashloop-bad-command-fix.yaml
```

### 📝 Interview Answer
> "First I'd check `kubectl logs` to see why the container is exiting. Then `kubectl describe pod` to see events and the exit code. Exit code tells me a lot — 1 means application error, 137 means OOMKilled, 139 means segfault. In this case, the startup command was wrong, which I'd fix in the deployment spec."

---

## Lab 2: ImagePullBackOff — Wrong Image

### 🔴 Break It
```bash
kubectl apply -f chaos-lab/02-imagepull-wrong-image.yaml
```

### 🔍 Debug It
```bash
# Step 1: Check pod status
kubectl get pods -n chaos-lab
# STATUS = ImagePullBackOff or ErrImagePull

# Step 2: Describe pod — look at Events
kubectl describe pod -l chaos=imagepull -n chaos-lab
# Events will show: "Failed to pull image" with the reason

# Step 3: Verify the image exists
# Check: Is the image name correct? Is the tag valid? Is the registry accessible?

# Step 4: Check imagePullSecrets if private registry
kubectl get pod -l chaos=imagepull -n chaos-lab -o jsonpath='{.items[0].spec.imagePullSecrets}'
```

### ✅ Fix It
```bash
kubectl apply -f chaos-lab/02-imagepull-wrong-image-fix.yaml
```

### 📝 Interview Answer
> "ImagePullBackOff means Kubernetes can't download the container image. I'd check three things: (1) is the image name and tag spelled correctly, (2) does the image actually exist in the registry, and (3) if it's a private registry, are the imagePullSecrets configured correctly. `kubectl describe pod` events tell you the exact error."

---

## Lab 3: Pod Stuck in Pending — Resource Starvation

### 🔴 Break It
```bash
kubectl apply -f chaos-lab/03-pending-no-resources.yaml
```

### 🔍 Debug It
```bash
# Step 1: Check pod status
kubectl get pods -n chaos-lab
# STATUS = Pending (stays there, never starts)

# Step 2: Describe pod — check Events
kubectl describe pod -l chaos=pending-resources -n chaos-lab
# Events: "0/1 nodes are available: insufficient cpu" or "insufficient memory"

# Step 3: Check node capacity
kubectl describe nodes | grep -A 5 "Allocated resources"

# Step 4: Check if there are resource quotas blocking it
kubectl get resourcequota -n chaos-lab
```

### ✅ Fix It
```bash
# Reduce the resource request to something the cluster can handle
kubectl apply -f chaos-lab/03-pending-no-resources-fix.yaml
```

### 📝 Interview Answer
> "Pending means the scheduler can't find a node to place the pod. Most common reasons: insufficient CPU/memory on all nodes, node selector or affinity that doesn't match any node, taints without matching tolerations, or a PVC that can't be bound. I'd check `kubectl describe pod` events first — they tell you exactly why scheduling failed."

---

## Lab 4: OOMKilled — Memory Limit Too Low

### 🔴 Break It
```bash
kubectl apply -f chaos-lab/04-oomkilled-memory.yaml
```

### 🔍 Debug It
```bash
# Step 1: Watch pod status
kubectl get pods -n chaos-lab -w
# You'll see: Running → OOMKilled → CrashLoopBackOff

# Step 2: Check the termination reason
kubectl get pod -l chaos=oomkill -n chaos-lab -o jsonpath='{.items[0].status.containerStatuses[0].lastState.terminated.reason}'
# Output: OOMKilled

# Step 3: Check the exit code
kubectl get pod -l chaos=oomkill -n chaos-lab -o jsonpath='{.items[0].status.containerStatuses[0].lastState.terminated.exitCode}'
# Output: 137 (128 + 9 = SIGKILL)

# Step 4: Check actual memory usage vs limit
kubectl top pod -n chaos-lab
# Compare with the limit set in the deployment

# Step 5: Check node-level OOM events
kubectl get events -n chaos-lab --sort-by='.lastTimestamp' | grep -i oom
```

### ✅ Fix It
```bash
kubectl apply -f chaos-lab/04-oomkilled-memory-fix.yaml
```

### 📝 Interview Answer
> "OOMKilled means the container exceeded its memory limit and was killed by the kernel. Exit code 137 confirms it (128 + SIGKILL). I'd check `kubectl top pod` to see actual usage, then either increase the memory limit or investigate the application for memory leaks. I always set requests equal to typical usage and limits at 1.5-2x that."

---

## Lab 5: Service Not Routing — Label Mismatch

### 🔴 Break It
```bash
kubectl apply -f chaos-lab/05-service-label-mismatch.yaml
```

### 🔍 Debug It
```bash
# Step 1: Check if service has endpoints
kubectl get endpoints chaos-svc-broken -n chaos-lab
# Output: <none> — no endpoints means no pods matched

# Step 2: Check service selector
kubectl get svc chaos-svc-broken -n chaos-lab -o jsonpath='{.spec.selector}'
# Shows what labels the service is looking for

# Step 3: Check pod labels
kubectl get pods -n chaos-lab --show-labels | grep svc-mismatch

# Step 4: Compare — the labels don't match!

# Step 5: Test connectivity from inside cluster
kubectl run test-curl --image=curlimages/curl -n chaos-lab --rm -it -- curl http://chaos-svc-broken:80
# Will fail — connection refused or timeout
```

### ✅ Fix It
```bash
kubectl apply -f chaos-lab/05-service-label-mismatch-fix.yaml
```

### 📝 Interview Answer
> "If a service isn't routing traffic, the first thing I check is `kubectl get endpoints <service>`. If endpoints are empty, the service selector doesn't match any pod labels. I compare the service's spec.selector with the pod's metadata.labels — they must match exactly. Also check if the pods are actually Ready, because unready pods are excluded from endpoints."

---

## Lab 6: DNS Resolution Failure — CoreDNS Broken

### 🔴 Break It
```bash
kubectl apply -f chaos-lab/06-dns-failure.yaml
```

### 🔍 Debug It
```bash
# Step 1: Try DNS resolution from inside a pod
kubectl exec -it dns-test-pod -n chaos-lab -- nslookup kubernetes.default
# Will fail or timeout

# Step 2: Check CoreDNS pods
kubectl get pods -n kube-system -l k8s-app=kube-dns
# Are they running? Are they ready?

# Step 3: Check CoreDNS logs
kubectl logs -n kube-system -l k8s-app=kube-dns

# Step 4: Check the pod's DNS config
kubectl exec -it dns-test-pod -n chaos-lab -- cat /etc/resolv.conf
# Should point to CoreDNS service IP

# Step 5: Test with external DNS directly
kubectl exec -it dns-test-pod -n chaos-lab -- nslookup google.com 8.8.8.8
# If this works but cluster DNS doesn't → CoreDNS issue
```

### ✅ Fix It
```bash
# Restore CoreDNS or fix the DNS policy
kubectl apply -f chaos-lab/06-dns-failure-fix.yaml
```

### 📝 Interview Answer
> "For DNS issues, I'd exec into the pod and run `nslookup <service-name>`. If that fails, I check if CoreDNS pods in kube-system are running and ready. Then check the pod's /etc/resolv.conf to verify it's pointing to the right nameserver. I also check CoreDNS logs for errors. A common issue is the pod's dnsPolicy being set incorrectly."

---

## Lab 7: Liveness Probe Failure — Constant Restarts

### 🔴 Break It
```bash
kubectl apply -f chaos-lab/07-liveness-probe-fail.yaml
```

### 🔍 Debug It
```bash
# Step 1: Watch the restarts count increasing
kubectl get pods -n chaos-lab -l chaos=liveness -w
# RESTARTS keeps increasing

# Step 2: Check events
kubectl describe pod -l chaos=liveness -n chaos-lab
# Events: "Liveness probe failed: HTTP probe failed with statuscode: 404"
# Events: "Container will be killed and recreated"

# Step 3: Check what the probe is checking
kubectl get pod -l chaos=liveness -n chaos-lab -o jsonpath='{.items[0].spec.containers[0].livenessProbe}'

# Step 4: Test the probe endpoint manually
kubectl exec -it <pod-name> -n chaos-lab -- curl localhost:80/wrong-health-path
# 404 — the path is wrong!
```

### ✅ Fix It
```bash
kubectl apply -f chaos-lab/07-liveness-probe-fail-fix.yaml
```

### 📝 Interview Answer
> "If a pod keeps restarting but logs show it's starting fine, I check the liveness probe. `kubectl describe pod` events will say 'Liveness probe failed' with the exact error. Common issues: wrong path, wrong port, timeout too short, or initialDelaySeconds too low for slow-starting apps. I'd also check readiness probes separately since those affect service traffic."

---

## Lab 8: Resource Quota Exhaustion — Deployment Can't Scale

### 🔴 Break It
```bash
kubectl apply -f chaos-lab/08-resource-quota-exhausted.yaml
```

### 🔍 Debug It
```bash
# Step 1: Check deployment status
kubectl get deployment quota-test -n chaos-lab
# READY shows fewer pods than DESIRED

# Step 2: Check replica set
kubectl get rs -n chaos-lab
# ReplicaSet shows desired > available

# Step 3: Check replica set events — THIS IS KEY
kubectl describe rs -n chaos-lab | grep -A 5 "Events"
# "Error creating: pods is forbidden: exceeded quota"

# Step 4: Check the quota
kubectl get resourcequota -n chaos-lab
# Shows used vs hard limits

# Step 5: Check HPA if auto-scaling
kubectl get hpa -n chaos-lab
```

### ✅ Fix It
```bash
kubectl apply -f chaos-lab/08-resource-quota-exhausted-fix.yaml
```

### 📝 Interview Answer
> "If a deployment won't scale, I check the ReplicaSet events — not just the pod events. The RS will say 'exceeded quota' or 'insufficient resources'. I also check `kubectl get resourcequota` in the namespace. For HPA issues, I check if metrics-server is running and if the HPA's target metrics are being scraped correctly."

---

## 🧹 Cleanup

```bash
# Remove all chaos lab resources
kubectl delete namespace chaos-lab
```

---

## 🎯 Practice Checklist

After completing all labs, you should be able to:

- [ ] Diagnose CrashLoopBackOff from logs and exit codes
- [ ] Fix ImagePullBackOff by verifying image names, tags, and registry auth
- [ ] Identify why pods are Pending (resources, selectors, taints)
- [ ] Recognize OOMKilled by exit code 137 and fix memory limits
- [ ] Debug service routing by checking endpoints and label selectors
- [ ] Troubleshoot DNS by testing CoreDNS and /etc/resolv.conf
- [ ] Fix liveness/readiness probe failures
- [ ] Identify resource quota exhaustion from ReplicaSet events

> **Tip:** Run through these labs 2-3 times until the debug commands are muscle memory. In an interview, the speed and confidence with which you describe these steps matters as much as the answer itself.

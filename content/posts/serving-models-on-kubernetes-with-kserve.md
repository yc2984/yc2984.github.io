+++
title = 'Serving models on Kubernetes with KServe'
title_html = 'Serving models on Kubernetes with <em>KServe</em>'
date = 2024-04-02T10:00:00+02:00
draft = false
summary = "Scale-to-zero sounds free until you meet the cold start. What KServe actually buys you, what it quietly costs, and the numbers from a real load test."
tags = ['kubernetes', 'kserve', 'knative', 'ml-infrastructure', 'model-serving']
categories = ['ML infrastructure']
aliases = ['/posts/kserve-end-to-end-guild/']
toc = true
+++

If you serve more than one model, you eventually hit the same fork in the road.
Bundle every model into one service and they share a fate: one lifecycle, one
memory limit, one autoscaling policy. The model having the worst afternoon
decides everyone's afternoon, and you can't give the expensive model more room
without giving it to all of them. Split them into a service per model and the
isolation problem goes away — replaced by a bill that scales linearly with the
number of models, most of which are idle most of the time.

[TODO: two or three sentences on your actual situation — how many models, what
the old setup was, what specifically hurt. This is the part readers will
recognise themselves in, and it's the one part I can't write for you.]

[KServe](https://kserve.dev/) claims you don't have to choose. Each model
becomes its own `InferenceService` with its own autoscaling policy, and when
nothing calls it, it scales to **zero** — no pods, no cost. Isolation with
per-model economics.

That claim is mostly true. This post is about the "mostly": what the stack is
actually made of, how to stand it up without the three mistakes I made, and what
happened when I pointed real load at it.

The short version, if you only read one line:

> **Scale-to-zero doesn't remove the cost. It moves it from your cloud bill to
> your p99.**

---

## What KServe actually is

The first thing worth understanding is that KServe is not a server. It's a thin,
opinionated layer of Kubernetes CRDs on top of a fairly tall stack, and most of
the behaviour people attribute to KServe — the autoscaling, the scale-to-zero,
the request buffering — is really Knative underneath it.

From the bottom up:

{{< diagram caption="Fig. 1 — one inference request. The activator only appears when replicas are at zero; everything warm skips it." >}}
<svg viewBox="0 0 700 470" role="img" aria-label="Request path: client, Istio ingress gateway, Knative activator when replicas are zero, model server pod, response. The autoscaler observes and scales from the side.">
  <defs>
    <marker id="a1" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 1 L 9 5 L 0 9" fill="none" stroke="currentColor" stroke-width="1.6"/>
    </marker>
    <pattern id="wait" width="6" height="6" patternUnits="userSpaceOnUse">
      <rect width="2" height="6" fill="currentColor" opacity="0.22"/>
    </pattern>
  </defs>

  <g font-family="DM Mono, monospace" font-size="10" letter-spacing="1.8" opacity="0.7">
    <text x="0" y="10">CONTROL PLANE</text>
    <text x="252" y="10">REQUEST PATH</text>
  </g>

  <g fill="none" stroke="currentColor">
    <rect x="0" y="120" width="176" height="46" stroke-width="1" opacity="0.55"/>
    <rect x="252" y="24"  width="286" height="50" stroke-width="1.4"/>
    <rect x="252" y="106" width="286" height="50" stroke-width="1.4"/>
    <rect x="252" y="188" width="286" height="62" stroke-width="1.4" fill="url(#wait)"/>
    <rect x="252" y="282" width="286" height="62" stroke-width="1.4"/>
  </g>
  <rect x="252" y="376" width="286" height="40" fill="currentColor"/>

  <g font-family="Hanken Grotesk, sans-serif" font-size="14" fill="currentColor">
    <text x="14"  y="141">Knative autoscaler</text>
    <text x="268" y="46">Client request</text>
    <text x="268" y="128">Istio ingress gateway</text>
    <text x="268" y="210">Knative activator</text>
    <text x="268" y="304">Model server pod</text>
  </g>
  <g font-family="DM Mono, monospace" font-size="9.5" letter-spacing="1.2" fill="currentColor" opacity="0.72">
    <text x="14"  y="157">KPA · RPS OR CONCURRENCY</text>
    <text x="268" y="62">gRPC h2c · ModelInfer</text>
    <text x="268" y="144">ROUTES INTO THE MESH</text>
    <text x="268" y="226">ONLY WHEN REPLICAS = 0</text>
    <text x="268" y="241">HOLDS THE REQUEST, WAKES THE POD</text>
    <text x="268" y="320">MLSERVER / TRITON / TORCHSERVE</text>
    <text x="268" y="335">READINESS GATES THE TRAFFIC</text>
  </g>
  <text x="268" y="401" font-family="Hanken Grotesk, sans-serif" font-size="14" fill="var(--paper)">Response</text>

  <g stroke="currentColor" stroke-width="1.4" fill="none">
    <line x1="395" y1="74"  x2="395" y2="102" marker-end="url(#a1)"/>
    <line x1="395" y1="156" x2="395" y2="184" marker-end="url(#a1)"/>
    <line x1="395" y1="250" x2="395" y2="278" marker-end="url(#a1)"/>
    <line x1="395" y1="344" x2="395" y2="372" marker-end="url(#a1)"/>
    <path d="M 538 131 H 596 V 313 H 546" marker-end="url(#a1)"/>
  </g>
  <path d="M 176 143 H 214 V 313 H 248" fill="none" stroke="currentColor" stroke-width="1" opacity="0.55" marker-end="url(#a1)"/>

  <g font-family="DM Mono, monospace" font-size="9.5" letter-spacing="1.4" fill="currentColor">
    <text x="606" y="208">WARM PATH</text>
    <text x="606" y="223" opacity="0.7">REPLICAS &gt; 0</text>
    <text x="606" y="238" opacity="0.7">SKIPS THE</text>
    <text x="606" y="253" opacity="0.7">ACTIVATOR</text>
    <text x="182" y="136" opacity="0.7">SCALES</text>
  </g>
</svg>
{{< /diagram >}}
And sitting beside all of it:

- **cert-manager** — issues the TLS certificates KServe's admission webhooks
  need. It isn't optional, and its failures look like unrelated timeouts, which
  is why it's worth naming here.
- **KServe** itself — the controller that turns one `InferenceService` into a
  Knative Service, a Deployment, a storage initialiser that pulls your model
  artifact, and the routing to reach it.

Why does this matter before you type a single `kubectl apply`? Because when
something misbehaves — and it will — the useful question is *which layer*. A
request that hangs for two seconds is the activator. A pod that never becomes
ready is the storage initialiser or your model format. A webhook error on apply
is cert-manager. Knowing the stack turns a mystery into a lookup.

### What you give up

Worth being explicit, because the docs are not:

- **Kubernetes tax.** You are now operating Knative, Istio and cert-manager,
  each with its own version-compatibility matrix. Upgrading one is a project.
- **A latency floor.** Even warm, requests pass through the ingress gateway and
  (depending on configuration) the activator. It is not free.
- **Cold starts.** The headline feature has a price tag, quantified below.

If you have two models and steady traffic, a plain Deployment behind a
HorizontalPodAutoscaler is a completely defensible answer and you should
probably stop reading. KServe earns its complexity when you have *many* models
with *spiky or sparse* traffic — which is exactly the situation where
scale-to-zero is worth real money.

---

## Standing it up

What follows is the install that worked, in order, with the reasoning. Versions
are pinned deliberately: Knative, Istio and KServe are mutually
version-sensitive, and mixing releases is the fastest way to a cluster that
comes up but doesn't serve.

| Component    | Version   |
|--------------|-----------|
| Knative Serving | 1.13.1 |
| net-istio    | 1.13.1    |
| cert-manager | 1.14.4    |
| KServe       | 0.12.0    |

**Prerequisites:** a Kubernetes cluster, `kubectl`, Helm, and a GCS bucket (any
object store KServe supports works — S3 and Azure Blob follow the same shape,
with a different secret).

### 0. A namespace for the models

```bash
kubectl create namespace kserve-test
```

This namespace is for *your* workloads. The platform components mostly install
elsewhere, which turns out to be the single biggest tripwire in the whole
process.

### 1. Knative Serving

CRDs first, then the controller. Applying them together is a race: the
controller's manifests reference types the API server doesn't know yet.

```bash
KN=github.com/knative/serving/releases/download/knative-v1.13.1

kubectl apply -f https://$KN/serving-crds.yaml
kubectl apply -f https://$KN/serving-core.yaml
```

{{< note "Where I lost an hour" >}}
Knative Serving belongs in the `knative-serving` namespace, which its manifest
creates for you. If you pass `-n kserve-test` here, the install *appears* to
succeed — objects are created, no errors — and then nothing ever reconciles your
models, because the controller isn't watching where you think it is. Apply these
without a namespace override and let the manifest place things.
{{< /note >}}

### 2. Istio, as Knative's networking layer

Knative needs a networking layer to program ingress. Istio is the best-trodden
option.

```bash
NI=github.com/knative/net-istio/releases/download/knative-v1.13.1

# CRDs first, again
kubectl apply -l knative.dev/crd-install=true -f https://$NI/istio.yaml
kubectl apply -f https://$NI/istio.yaml

# then the controller that teaches Knative to drive Istio
kubectl apply -f https://$NI/net-istio.yaml
```

Verify before moving on. This is a real checkpoint, not a formality — a
half-installed networking layer produces symptoms that look like model problems
for the next hour.

```bash
kubectl get pods -n knative-serving
```

You want six pods `Running`: `activator`, `autoscaler`, `controller`,
`webhook`, `net-istio-controller` and `net-istio-webhook`. If the webhook pods
aren't ready, stop — everything downstream will fail at admission.

### 3. cert-manager

KServe's admission webhooks need certificates. cert-manager issues them.

```bash
CM=github.com/cert-manager/cert-manager/releases/download/v1.14.4

kubectl apply -f https://$CM/cert-manager.crds.yaml

helm repo add jetstack https://charts.jetstack.io
helm repo update
helm install cert-manager-kserve jetstack/cert-manager \
  --namespace cert-manager --create-namespace \
  --version v1.14.4
```

{{< note "A correction to my original notes" >}}
I first installed cert-manager into `kserve-test` with `&` instead of `&&`
between the two commands — so the repo add and the install raced, and the install
ran against a repo that might not exist yet. It worked by luck. Use `&&`, and
give cert-manager its own namespace; it's cluster-scoped infrastructure, not part
of your app.
{{< /note >}}

### 4. KServe

```bash
helm install kserve-crd oci://ghcr.io/kserve/charts/kserve-crd \
  --version v0.12.0 -n kserve-test

helm install kserve oci://ghcr.io/kserve/charts/kserve \
  --version v0.12.0 --values values.yaml -n kserve-test
```

### 5. Credentials for the model store

KServe pulls model artifacts at pod startup using a storage initialiser
container. It needs credentials, supplied as a secret. For GCS, that's a service
account key with read access to the bucket:

```bash
kubectl create secret generic storage-config \
  --from-file=gcloud-application-credentials.json=<path-to-key> \
  -n kserve-test
```

Two non-negotiable details: the key inside the secret **must** be named
`gcloud-application-credentials.json`, and the secret must live in the same
namespace as the `InferenceService`. Get either wrong and the pod sits in
`Init:0/1` with a permission error buried in the init container's logs — a good
five minutes of confusion the first time.

---

## Deploying a model

Upload the artifact, then declare an `InferenceService` that points at it.

```bash
gcloud config set project <your-project-id>
gsutil mb gs://<your-bucket>
gsutil cp model.ubj gs://<your-bucket>/<model-name>/
```

Two conventions that are easy to miss and produce unhelpful errors:

1. **`storageUri` is a *directory*, not a file.** Point it at the prefix
   containing the model, with no filename.
2. **The file must be named `model.<ext>`.** The runtime discovers the artifact
   by that name — `my_forecast_v3.ubj` will not be found.

```yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: my-model
  namespace: kserve-test
  annotations:
    serving.kserve.io/secretName: storage-config
spec:
  predictor:
    minReplicas: 0          # <- this is the whole point
    scaleMetric: rps
    scaleTarget: 10         # target 10 rps per replica
    model:
      modelFormat:
        name: xgboost
      protocolVersion: v2
      storageUri: gs://<your-bucket>/<model-name>/
      resources:
        requests:
          cpu: 100m
          memory: 200Mi
        limits:
          cpu: 500m
          memory: 500Mi
      ports:
        - name: h2c        # Knative requires this exact name for gRPC
          protocol: TCP
          containerPort: 9000
      readinessProbe:
        httpGet:
          path: /v2/models/my-model/ready
          port: 8080
```

Three of those lines deserve a sentence each:

- **`minReplicas: 0`** is the feature. Everything else in this post is
  downstream of it.
- **`name: h2c`** on the port is not decoration. Knative uses the port name to
  decide protocol, and gRPC over HTTP/2 cleartext must be called `h2c`. Name it
  `grpc` and requests fail in a way that points nowhere useful.
- **The `readinessProbe`** matters more than it looks. Without it, the pod is
  marked ready as soon as the container starts — but the model may still be
  loading, so traffic arrives before the model can answer. The next section is
  entirely about what that looks like.

Then:

```bash
kubectl apply -f my-model.yaml -n kserve-test
```

---

## Load testing, and the number that surprised me

I used [`ghz`](https://ghz.sh/) for gRPC load generation, running it as a Job
inside the cluster so the measurement isn't dominated by internet latency. It
needs KServe's `grpc_predict_v2.proto`, mounted as a ConfigMap:

```bash
kubectl create configmap proto-files \
  --from-file=grpc_predict_v2.proto -n kserve-test
```

The interesting part of the `ghz` config is the load schedule — a *step* ramp
rather than a constant rate, because a constant rate lets the autoscaler settle
and hides exactly the behaviour I wanted to see:

```json
{
  "load-schedule": "step",
  "load-start": 10,
  "load-end": 20,
  "load-step": 5,
  "load-step-duration": "5s",
  "timeout": "30s",
  "max-duration": "180s"
}
```

The full driver script — which deploys the model at a given `scaleMetric` /
`scaleTarget`, waits for it, then runs the Job — is in the repo:
[`performance_test/model_infer-ghz.sh`](https://github.com/yc2984/kserve-poc).

### The results

Stepping to 20 rps against a model with `minReplicas: 0`:

{{< figures caption="Fig. 2 — ghz, step load 10→20 rps over 180 s, minReplicas 0" items="p50=1.70 s|p99=2.70 s|succeeded=57 %" >}}

| Metric | Value |
|--------|-------|
| Requests | 1,809 |
| Achieved throughput | 15.07 rps |
| p50 | 1.70 s |
| p90 | 2.09 s |
| p99 | 2.70 s |
| Fastest | 110 ms |
| Successful (`OK`) | 1,030 (**57%**) |

And the error distribution, which is the actual story:

```
[InvalidArgument]   739   "Model my-model with version is not ready yet"
[DeadlineExceeded]   19
[Unavailable]        21
```

**Forty-three percent of requests failed, and almost all of them for one
reason: the model wasn't loaded yet.** The autoscaler did its job — it saw
traffic and started a pod. But starting a pod means pulling an image, running
the storage initialiser to fetch the artifact from GCS, starting the runtime,
and loading the model. Until that finishes, the pod is up and answering — with
"not ready".

Note also the gap between the fastest request (110 ms, a warm pod) and p50
(1.70 s). That spread *is* the cold start. On a steady-state benchmark it
disappears entirely, which is precisely why a steady-state benchmark would have
told me the wrong thing.

### What the failures actually mean

Three separate problems wearing three confusing error codes:

- **`InvalidArgument` — "not ready yet".** The model server is reachable before
  the model is usable. This is what the `readinessProbe` above fixes: gate
  readiness on `/v2/models/<name>/ready` rather than on the process starting,
  and Knative won't route to the pod until it can actually answer. Adding it was
  the single highest-value change I made.
- **`DeadlineExceeded`.** The activator held the request while a pod came up,
  and the 30 s client timeout expired first. The fix isn't a longer timeout —
  it's a shorter cold start.
- **`Unavailable`.** Connections dropped mid-scale-up. Some of this is
  unavoidable during a topology change; the rest is Istio and the client not
  agreeing about connection reuse.

### Making cold starts smaller

In rough order of leverage:

1. **Fix readiness first.** Until the probe is right, you're measuring your own
   misconfiguration rather than the platform.
2. **Shrink the image.** Image pull is often the largest single term. A
   slimmer runtime image beats almost any tuning.
3. **Keep the artifact close.** Same-region bucket; small model files. An
   XGBoost model is kilobytes, so this term is negligible here — for anything
   with weights in the gigabytes it dominates everything else.
4. **Then choose your poison.** `minReplicas: 1` eliminates cold starts and the
   savings with them. Knative's scale-down delay
   (`scale-to-zero-grace-period`) is the middle ground: stay warm through gaps
   in bursty traffic, still go to zero overnight.

---

## So: worth it?

For sparse, bursty traffic across many models — yes, clearly. Per-model
isolation and a bill that tracks actual use are hard to get any other way, and
the operational cost is a one-time investment rather than a recurring one.

For a handful of models with steady traffic, no. You'd be operating Knative,
Istio and cert-manager to solve a problem a Deployment and an HPA already
solve, and paying a latency floor for the privilege.

The thing I'd want to know before starting, and didn't: **cold starts are not
an implementation detail you tune away later — they're a product decision you
make up front.** Either your callers tolerate a multi-second first request, or
you keep something warm and give back part of the saving. KServe makes that
trade-off cheap to *express*. It doesn't make it go away.

[TODO: which way did you actually go in the end — scale to zero, minReplicas: 1,
or the grace-period middle ground? Ending on your real decision is worth more
than any of the above.]

---

*Code, model configs and the load-test harness:
[github.com/yc2984/kserve-poc](https://github.com/yc2984/kserve-poc).*

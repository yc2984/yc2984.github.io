+++
title = 'Serving models on Kubernetes with KServe'
title_html = 'Serving models on Kubernetes with <em>KServe</em>'
date = 2024-04-02T10:00:00+02:00
draft = false
summary = "Scale-to-zero sounds free until you meet the cold start. What KServe actually buys you, what it quietly costs, and why we turned the headline feature off in the end."
labels = ['Tech', 'AI']
tags = ['kubernetes', 'kserve', 'knative', 'ml-infrastructure', 'model-serving']
categories = ['ML infrastructure']
aliases = ['/posts/kserve-end-to-end-guild/']
toc = true
+++

Two and a half thousand models in each cloud runtime. That number is what makes
this decision interesting, because past a certain scale the usual fork in the
road stops being a trade-off and starts being arithmetic. Bundle everything into
one service and every model shares a fate — one lifecycle, one memory limit, one
autoscaling policy — so whichever model is having the worst afternoon decides
everyone's afternoon. Split them into a service per model and the isolation
problem disappears, replaced by a bill for 2,500 deployments, nearly all of them
idle nearly all of the time.

[KServe](https://kserve.dev/) claims you don't have to choose. Each model becomes
its own `InferenceService` with its own autoscaling policy, and when nothing
calls it, it scales to **zero** — no pods, no cost. Isolation with per-model
economics.

That claim is mostly true. This post is about the "mostly": what the stack is
actually made of, how to stand it up without the three mistakes I made, what
happened when I pointed real load at it, and why we ended up not using the
feature we came for.

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

The full driver script deploys the model at a given `scaleMetric` /
`scaleTarget`, waits for it to become ready, then runs the Job.

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

{{< diagram caption="Fig. 2 — response time of the 1,030 requests that succeeded. One series, so one colour and no legend; only the peak carries a number." >}}
<svg viewBox="0 0 700 292" role="img" aria-label="Histogram of successful response times. The tallest bucket, 1.50 to 1.78 seconds, holds 453 requests. Median 1.70 seconds, 99th percentile 2.70 seconds.">
  <g stroke="currentColor" stroke-width="1" opacity="0.2">
    <line x1="48" y1="20" x2="700" y2="20"/>
    <line x1="48" y1="87.5" x2="700" y2="87.5"/>
    <line x1="48" y1="154" x2="700" y2="154"/>
  </g>
  <line x1="48" y1="220" x2="700" y2="220" stroke="currentColor" stroke-width="1"/>

  <g font-family="DM Mono, monospace" font-size="9.5" fill="currentColor" opacity="0.7" text-anchor="end" style="font-variant-numeric: tabular-nums">
    <text x="38" y="23">450</text><text x="38" y="91">300</text>
    <text x="38" y="157">150</text><text x="38" y="223">0</text>
  </g>
  <text x="48" y="11" font-family="DM Mono, monospace" font-size="9" letter-spacing="1.5" fill="currentColor" opacity="0.7">REQUESTS</text>

  <g fill="currentColor">
    <rect x="61.6" y="218.0" width="32" height="2.0" rx="1.0"/>
    <rect x="120.9" y="217.4" width="32" height="2.6" rx="1.3"/>
    <rect x="180.2" y="213.4" width="32" height="6.6" rx="3.3"/>
    <rect x="239.5" y="215.1" width="32" height="4.9" rx="2.4"/>
    <rect x="298.8" y="209.4" width="32" height="10.6" rx="4.0"/>
    <rect x="358.1" y="154.7" width="32" height="65.3" rx="4.0"/>
    <rect x="417.4" y="20.0" width="32" height="200.0" rx="4.0"/>
    <rect x="476.7" y="101.7" width="32" height="118.3" rx="4.0"/>
    <rect x="536.0" y="192.6" width="32" height="27.4" rx="4.0"/>
    <rect x="595.3" y="209.0" width="32" height="11.0" rx="4.0"/>
    <rect x="654.6" y="212.5" width="32" height="7.5" rx="3.8"/>
  </g>

  <text x="433.4" y="12" font-family="Hanken Grotesk, sans-serif" font-size="13" font-weight="600" fill="currentColor" text-anchor="middle">453</text>

  <g stroke="currentColor" stroke-width="1" opacity="0.5">
    <line x1="445.4" y1="20" x2="445.4" y2="226"/>
    <line x1="658.1" y1="20" x2="658.1" y2="226"/>
  </g>

  <g font-family="DM Mono, monospace" font-size="9.5" fill="currentColor" opacity="0.7" text-anchor="middle" style="font-variant-numeric: tabular-nums">
      <text x="77.7" y="240">0.11</text>
      <text x="196.2" y="240">0.67</text>
      <text x="314.8" y="240">1.23</text>
      <text x="433.4" y="240">1.78</text>
      <text x="552.0" y="240">2.34</text>
      <text x="670.6" y="240">2.90</text>
  </g>
  <g font-family="DM Mono, monospace" font-size="9" letter-spacing="1" fill="currentColor" text-anchor="middle">
    <text x="445.4" y="258">P50 1.70s</text>
    <text x="658.1" y="258">P99 2.70s</text>
  </g>
  <text x="374" y="280" font-family="DM Mono, monospace" font-size="9" letter-spacing="1.5" fill="currentColor" opacity="0.7" text-anchor="middle">RESPONSE TIME (SECONDS)</text>
</svg>
{{< /diagram >}}

And the outcome breakdown, which is the actual story:

{{< diagram caption="Fig. 3 — outcome by gRPC status code. The two thin segments are too narrow to label, so the table below carries them." >}}
<svg viewBox="0 0 700 96" role="img" aria-label="Of 1809 requests: 1030 OK, 739 InvalidArgument meaning the model was not ready, 21 Unavailable, 19 DeadlineExceeded.">
  <rect x="0"     y="6" width="395.1" height="44" fill="#141C93"/>
  <rect x="397.1" y="6" width="283.5" height="44" fill="#1F2BE0"/>
  <rect x="682.6" y="6" width="8.1"   height="44" fill="#5560E5"/>
  <rect x="692.7" y="6" width="7.3"   height="44" fill="#9AA1EE"/>

  <g font-family="DM Mono, monospace" font-size="10" letter-spacing="1" fill="#F0EBDE">
    <text x="14"  y="32">OK &#183; 1,030</text>
    <text x="411" y="32">NOT READY &#183; 739</text>
  </g>

  <g font-family="DM Mono, monospace" font-size="9.5" fill="currentColor">
    <rect x="0"   y="72" width="9" height="9" fill="#141C93"/><text x="14"  y="80">OK</text>
    <rect x="46"  y="72" width="9" height="9" fill="#1F2BE0"/><text x="60"  y="80">InvalidArgument</text>
    <rect x="176" y="72" width="9" height="9" fill="#5560E5"/><text x="190" y="80">Unavailable</text>
    <rect x="280" y="72" width="9" height="9" fill="#9AA1EE"/><text x="294" y="80">DeadlineExceeded</text>
  </g>
</svg>
{{< /diagram >}}

| Status | Requests | Share |
|--------|---------:|------:|
| `OK` | 1,030 | 56.9% |
| `InvalidArgument` — model not ready | 739 | 40.9% |
| `Unavailable` | 21 | 1.2% |
| `DeadlineExceeded` | 19 | 1.1% |

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

Here is the honest ending: we kept KServe and turned off the feature we came for.

`minReplicas: 0` is not set anywhere in production. The deployment runs a
constant four pods, always warm, and the cold-start problem is solved the
expensive way — by never having one.

Which sounds like a failed experiment, and isn't. The section above *is* the
result. Forty-three percent of requests failing on a cold start is not a number
you tune away next sprint; it's an answer. Finding it in a load test cost an
afternoon. Finding it in production, in front of callers who had been told the
model was available, would have cost considerably more — and we would have found
it eventually either way, because scale-to-zero doesn't degrade gracefully. It
works perfectly right up until traffic arrives at an empty deployment.

So the value wasn't the saving. It was learning the price of the saving before
committing to it, and then deciding not to pay.

The thing I'd want to know before starting, and didn't: **cold starts are not an
implementation detail you tune away later — they're a product decision you make
up front.** Either your callers tolerate a multi-second first request, or you
keep something warm and hand back part of the saving. KServe makes that trade-off
cheap to *express*, and cheap to measure. It does not make it go away.

We made ours. It just wasn't the one the feature list suggested.

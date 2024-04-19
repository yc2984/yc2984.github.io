# kserve-poc

This is a proof of concept for using [Kserve](https://kserve.dev/) as model serving infrastructure. Its ability to scale models individually and also scales to zero is helpful for performance and cost.   

## Installation

### Pre-requisites
- A k8s cluster
- kubectl
- Helm
- A GCS bucket

### Installing Kserve

#### 0. Create a namespace for testing
```
kubectl create namespace kserve-test
```

Reference doc: https://kserve.github.io/website/master/admin/serverless/serverless/ 
#### 1. Install Knative Serving

Reference: https://knative.dev/docs/install/yaml-install/serving/install-serving-with-yaml/#install-the-knative-serving-component

##### 1.1 Install Knative Serving CRDs
```
kubectl apply -f https://github.com/knative/serving/releases/download/knative-v1.13.1/serving-crds.yaml -n kserve-test 
```
##### 1.2 Install Knative Serving
Please note that the namespace here needs to be knative-serving, not the namespace that you created for testing. 
```
kubectl apply -f https://github.com/knative/serving/releases/download/knative-v1.13.1/serving-core.yaml -n knative-serving
```

#### 2. Install Istio

Reference: https://knative.dev/docs/install/yaml-install/serving/install-serving-with-yaml/#install-a-networking-layer

##### 2.1 Install Istio and CRD
```
kubectl apply -l knative.dev/crd-install=true -f https://github.com/knative/net-istio/releases/download/knative-v1.13.1/istio.yaml
kubectl apply -f https://github.com/knative/net-istio/releases/download/knative-v1.13.1/istio.yaml
```
##### 2.2 Install Istio controller
```
kubectl apply -f https://github.com/knative/net-istio/releases/download/knative-v1.13.1/net-istio.yaml
```
##### 2.3 Verify the installation
```
kubectl get pods -n knative-serving
```
You should see six pods running.

#### 3. Install Certificate Manager
##### 3.1 Install the cert-manager CRDs
```
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.14.4/cert-manager.crds.yaml
```
##### 3.2 Create the namespace for cert-manager
```
helm repo add jetstack https://charts.jetstack.io & helm install cert-manager-kserve --namespace kserve-test --version v1.14.4 jetstack/cert-manager
```
#### 4. Install Kserve
##### 4.1 Install Kserve CRD
```
helm install kserve-crd oci://ghcr.io/kserve/charts/kserve-crd --version v0.12.0 -n kserve-test
```
##### 4.2 Install Kserve
```
helm install kserve oci://ghcr.io/kserve/charts/kserve --version v0.12.0 --values values.yaml -n kserve-test
```
##### 5. Set up a k8s secret
This is for kserve to access the model stored in GCS. Create a key from a service account which has access to the GCS bucket. Note, the key file needs to be named `gcloud-application-credentials.json`.
```
kubectl create secret generic storage-config --from-file=<path-to-key-file>/gcloud-application-credentials.json -n kserve-test
```
##### 6. Create a GCS bucket for storing models
Make sure you are in the correct GCP project. 
```
gcloud config set project <your-project-id>
```
```
gsutil mb gs://<your-bucket>
```

## Deploy a model
### 1. Copy your model(s) to GCS
```
gsutil cp cluster_2_xgboost_forecast/model.ubj gs://<your-bucket>/<model-name>/
```
There is a sample model in the `cluster_2_xgboost_forecast` folder.
Note that the model file's name needs to be called model.xxx.
### 2. Apply the model config to k8s
There are a few examples in the `model_configs` dir.
Modify the yaml files to match with your model's path in GCS.
```
kubectl apply -f <path-to-your-model-config>.yaml -n kserve-test
```
### 3. Invoking the deployment with grpcurl (Optional)
Mount the volume:
`kubectl create configmap proto-files --from-file=grpc_predict_v2.proto -n kserve-test`

`export MODEL_NAME=<your-model-name>`
`export CONTENT_LENGTH=<content-length>`
```
./grpcurl/model_infer.sh $MODEL_NAME $CONTENT_LENGTH
```
You can check the pod `calling-<your-model-name>`

Known issue: when the min replica is set to zero, you will get this error for the first call(s) would get InvalidArgument error.
https://github.com/kserve/kserve/issues/2882
https://github.com/knative/serving/blob/main/docs/scaling/SYSTEM.md#scaling-from-zero
```
 ERROR:                                                                                                                                │
│   Code: InvalidArgument                                                                                                               │
│   Message: Model my-model with version  is not ready yet. 
```

***

## Running Performance Tests
To start a performance test, you need to run the following command:
`export MODEL_NAME=<your-model-name>`
`export CONTENT_LENGTH=38`
`export CONCURRENCY=20`
`export RPM=20`

```bash
.performance_test/model_infer-ghz.sh $MODEL_NAME $CONTENT_LENGTH $CONCURRENCY $RPM
```
Example result: 
```
│ Summary:                                                                                                                   │
│   Count:    1809                                                                                                           │
│   Total:    120.00 s                                                                                                       │
│   Slowest:    2.90 s                                                                                                       │
│   Fastest:    109.63 ms                                                                                                    │
│   Average:    1.25 s                                                                                                       │
│   Requests/sec:    15.07                                                                                                   │
│                                                                                                                            │
│ Response time histogram:                                                                                                   │
│   109.631  [1]   |                                                                                                         │
│   388.539  [6]   |∎                                                                                                        │
│   667.448  [15]  |∎                                                                                                        │
│   946.356  [11]  |∎                                                                                                        │
│   1225.264 [24]  |∎∎                                                                                                       │
│   1504.173 [148] |∎∎∎∎∎∎∎∎∎∎∎∎∎                                                                                            │
│   1783.081 [453] |∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎                                                                 │
│   2061.989 [268] |∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎                                                                                 │
│   2340.898 [62]  |∎∎∎∎∎                                                                                                    │
│   2619.806 [25]  |∎∎                                                                                                       │
│   2898.714 [17]  |∎∎                                                                                                       │
│                                                                                                                            │
│ Latency distribution:                                                                                                      │
│   10 % in 1.40 s                                                                                                           │
│   25 % in 1.60 s                                                                                                           │
│   50 % in 1.70 s                                                                                                           │
│   75 % in 1.80 s                                                                                                           │
│   90 % in 2.09 s                                                                                                           │
│   95 % in 2.30 s                                                                                                           │
│   99 % in 2.70 s                                                                                                           │
│                                                                                                                            │
│ Status code distribution:                                                                                                  │
│   [DeadlineExceeded]   19 responses                                                                                        │
│   [InvalidArgument]    739 responses                                                                                       │
│   [OK]                 1030 responses                                                                                      │
│   [Unavailable]        21 responses                                                                                        │
│                                                                                                                            │
│ Error distribution:                                                                                                        │
│   [20]    rpc error: code = Unavailable desc = error reading from server: read tcp 10.96.15.22:42192->10.100.9.175:80: use │
│   [1]     rpc error: code = Unavailable desc = upstream request timeout                                                    │
│   [19]    rpc error: code = DeadlineExceeded desc = context deadline exceeded                                              │
│   [739]   rpc error: code = InvalidArgument desc = Model my-model with version  is not ready yet. 
```

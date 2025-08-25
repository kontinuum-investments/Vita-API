#!/bin/bash

kubectl delete -f deploy.yml || kubectl delete pods --all || true

kubectl apply -f config-map.yml
kubectl apply -f deploy.yml

kubectl wait --for=condition=ready pod -l app=citadel --timeout=300s
kubectl logs -f -l app=citadel --all-containers=true --prefix
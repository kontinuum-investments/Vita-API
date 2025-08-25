#!/bin/bash

kubectl apply -f config-map.yml
kubectl delete -f deploy.yml || true
kubectl apply -f deploy.yml

kubectl wait --for=condition=ready pod -l app=citadel --timeout=300s
kubectl logs -f -l app=citadel --all-containers=true --prefix
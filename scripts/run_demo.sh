#!/bin/bash
set -e

echo "Applying namespace..."
kubectl apply -f k8s/namespace.yaml

echo "Applying RBAC..."
kubectl apply -f k8s/rbac.yaml

echo "Applying deployment..."
kubectl apply -f k8s/deployment.yaml

echo "Applying service..."
kubectl apply -f k8s/service.yaml

echo "Done. Check pod status:"
kubectl get pods -n autofix-demo
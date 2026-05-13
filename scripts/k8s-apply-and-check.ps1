# EventHub: build Compose images, apply k8s/, show pod status.
# If app pods show ErrImageNeverPull, Docker Desktop must expose images to the
# cluster (see README "On Kubernetes" — kubeadm vs kind / containerd store).
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Host "== docker compose build ==" -ForegroundColor Cyan
docker compose build

Write-Host "`n== kubectl apply ==" -ForegroundColor Cyan
kubectl apply -k k8s/

Write-Host "`n== quick image visibility test (Never) ==" -ForegroundColor Cyan
kubectl delete pod eventhub-imgcheck --ignore-not-found 2>$null
kubectl run eventhub-imgcheck `
  --image=eventhub-main-booking-service:latest `
  --image-pull-policy=Never `
  --restart=Never `
  --command -- /bin/sh -c "echo ok; sleep 3" 2>$null
Start-Sleep -Seconds 6
kubectl get pod eventhub-imgcheck -o wide 2>$null
kubectl describe pod eventhub-imgcheck 2>$null | Select-String -Pattern "ErrImageNeverPull|Started|Completed|Reason" | ForEach-Object { $_.Line }
kubectl delete pod eventhub-imgcheck --ignore-not-found 2>$null

Write-Host "`n== kubectl get pods ==" -ForegroundColor Cyan
kubectl get pods -o wide

# Workload Identity Federation Setup Script
# AWS Lambda ↔ Google Cloud Vertex AI

Write-Host "🌉 Workload Identity Federation Setup" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green

Write-Host "`n📋 What this does:" -ForegroundColor Yellow
Write-Host "• Connects AWS Lambda to Google Cloud Vertex AI" -ForegroundColor White
Write-Host "• Uses short-lived tokens (no long-lived credentials)" -ForegroundColor White
Write-Host "• Automatically handles authentication" -ForegroundColor White
Write-Host "• More secure than service account keys" -ForegroundColor White

Write-Host "`n🔧 Prerequisites:" -ForegroundColor Yellow
Write-Host "1. Google Cloud CLI installed and authenticated" -ForegroundColor White
Write-Host "2. AWS CLI installed and configured" -ForegroundColor White
Write-Host "3. Google Cloud project with Vertex AI enabled" -ForegroundColor White

Write-Host "`n🚀 Quick Setup Steps:" -ForegroundColor Yellow
Write-Host "1. Run: gcloud auth login" -ForegroundColor White
Write-Host "2. Run: gcloud config set project easy-video-share" -ForegroundColor White
Write-Host "3. Follow the detailed guide in 'workload-identity-setup.md'" -ForegroundColor White

Write-Host "`n💡 Key Commands:" -ForegroundColor Yellow
Write-Host "• Create Workload Identity Pool" -ForegroundColor White
Write-Host "• Create AWS Provider" -ForegroundColor White
Write-Host "• Create Service Account" -ForegroundColor White
Write-Host "• Grant Permissions" -ForegroundColor White

Write-Host "`n🔐 Security Benefits:" -ForegroundColor Yellow
Write-Host "✅ No long-lived credentials" -ForegroundColor Green
Write-Host "✅ Automatic token rotation" -ForegroundColor Green
Write-Host "✅ Fine-grained permissions" -ForegroundColor Green
Write-Host "✅ Audit trail" -ForegroundColor Green

Write-Host "`n💰 Cost:" -ForegroundColor Yellow
Write-Host "• Workload Identity Federation: FREE" -ForegroundColor Green
Write-Host "• Only pay for Vertex AI usage" -ForegroundColor White

Write-Host "`n📖 Next Steps:" -ForegroundColor Yellow
Write-Host "1. Open workload-identity-setup.md" -ForegroundColor White
Write-Host "2. Run the setup commands" -ForegroundColor White
Write-Host "3. Update terraform.tfvars" -ForegroundColor White
Write-Host "4. Deploy: terraform apply" -ForegroundColor White

Write-Host "`n✅ Ready to connect AWS and Google Cloud securely!" -ForegroundColor Green 
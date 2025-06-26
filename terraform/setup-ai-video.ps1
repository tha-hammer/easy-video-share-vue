# AI Video Generation Setup Script
# This script helps you set up Google Cloud for AI video generation

Write-Host "🚀 AI Video Generation Setup" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green

Write-Host "`n📋 Prerequisites:" -ForegroundColor Yellow
Write-Host "1. Google Cloud account (free tier available)" -ForegroundColor White
Write-Host "2. OpenAI API key" -ForegroundColor White
Write-Host "3. Billing enabled on Google Cloud project" -ForegroundColor White

Write-Host "`n🔧 Setup Steps:" -ForegroundColor Yellow
Write-Host "1. Follow the guide in 'setup-google-cloud.md'" -ForegroundColor White
Write-Host "2. Update terraform.tfvars with your credentials" -ForegroundColor White
Write-Host "3. Run: terraform apply -auto-approve" -ForegroundColor White

Write-Host "`n💰 Cost Estimate:" -ForegroundColor Yellow
Write-Host "- Vertex AI Veo 2: ~$0.05 per second" -ForegroundColor White
Write-Host "- OpenAI API: ~$0.03 per 1K tokens" -ForegroundColor White
Write-Host "- 30-second video: ~$1.50-3.00" -ForegroundColor White

Write-Host "`n📖 Next Steps:" -ForegroundColor Yellow
Write-Host "1. Open setup-google-cloud.md for detailed instructions" -ForegroundColor White
Write-Host "2. Configure your Google Cloud project" -ForegroundColor White
Write-Host "3. Update terraform.tfvars with real credentials" -ForegroundColor White
Write-Host "4. Deploy the infrastructure" -ForegroundColor White

Write-Host "`n✅ Ready to proceed!" -ForegroundColor Green
Write-Host "Open setup-google-cloud.md to get started." -ForegroundColor Cyan 
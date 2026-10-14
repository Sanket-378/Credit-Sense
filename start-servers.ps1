# Credit Sense - Start Both Servers
Write-Host "🚀 Starting Credit Sense Application..." -ForegroundColor Cyan
Write-Host ""

# Start Backend
Write-Host "📡 Starting Backend Server (FastAPI)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; python main.py"
Start-Sleep -Seconds 3

# Start Frontend
Write-Host "🌐 Starting Frontend Server (React + Vite)..." -ForegroundColor Blue
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev"
Start-Sleep -Seconds 3

Write-Host ""
Write-Host "✅ Both servers are starting!" -ForegroundColor Green
Write-Host ""
Write-Host "🔗 Backend API: http://localhost:8000" -ForegroundColor Yellow
Write-Host "🔗 API Docs: http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host "🔗 Frontend: http://localhost:3000" -ForegroundColor Yellow
Write-Host ""
Write-Host "📝 Press Ctrl+C in each terminal window to stop the servers" -ForegroundColor Magenta

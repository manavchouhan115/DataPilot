$bodies = @(
    "Extract dataset from data/input.csv, make Name lowercase, save to data/d1.db as users",
    "Extract from data/input.csv, uppercase Country, save to data/d2.db as clients",
    "Load data/input.csv, lowercase Email, save to data/d3.db as records",
    "Grab data/input.csv to data/d4.db table output",
    "Read data/input.csv, make Name uppercase, table people in data/d5.db"
)

foreach ($nl in $bodies) {
    $body = @{ nl_description = $nl } | ConvertTo-Json
    $res = Invoke-RestMethod -Uri "http://localhost:8000/pipeline" -Method Post -Body $body -ContentType "application/json"
    Write-Host "Started pipeline: $($res.pipeline_id)"
    
    # Auto-approve
    Start-Sleep -Seconds 3
    Invoke-RestMethod -Uri "http://localhost:8000/pipeline/$($res.pipeline_id)/approve" -Method Post
    Write-Host "Approved: $($res.pipeline_id)"
}

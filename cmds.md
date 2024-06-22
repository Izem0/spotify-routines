# Build the image
$routine = "update_top_songs"  # get_new_albums update_release_radar update_top_songs

docker build -f "$routine.Dockerfile" --platform linux/amd64 -t "spotify-$routine" .

# Start the Docker image (use PowerShell)
docker run --platform linux/amd64 -d -v "$HOME\.aws-lambda-rie:/aws-lambda" -p 9000:8080 --entrypoint /aws-lambda/aws-lambda-rie --name "spotify-$routine" "spotify-$routine" /usr/local/bin/python -m awslambdaric "app.routines.$routine.handler"

# Post an event to the local endpoint (use PowerShell)
Invoke-WebRequest -Uri "http://localhost:9000/2015-03-31/functions/function/invocations" -Method Post -Body '{}' -ContentType "application/json"


# [Extra] Download the runtime interface emulator (x86-64 architecture) (use PowerShell)
$dirPath = "$HOME\.aws-lambda-rie"
if (-not (Test-Path $dirPath)) {
    New-Item -Path $dirPath -ItemType Directory
}

$downloadLink = "https://github.com/aws/aws-lambda-runtime-interface-emulator/releases/latest/download/aws-lambda-rie"
$destinationPath = "$HOME\.aws-lambda-rie\aws-lambda-rie"
Invoke-WebRequest -Uri $downloadLink -OutFile $destinationPath

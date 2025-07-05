@echo off
echo 🔁 Starting Flask App...
start cmd /k "cd /d D:\Nguyen_Duc_Hoang_Phuc\Lab\denoise_homework - submit && call conda activate anaconda && python app.py"

timeout /t 6

echo 🌐 Launching Ngrok tunnel...
start cmd /k "cd /d C:\Users\ndhph\Downloads\ngrok-v3-stable-windows-amd64 && ngrok http 5000"

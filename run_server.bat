@echo off
title Adaptive AI Trading System - Backend Server
cd /d "%~dp0"
echo =======================================================
echo Starting Adaptive AI Trading Decision-Support Server...
echo Terminal UI:  http://127.0.0.1:8000/dashboard
echo API Docs:     http://127.0.0.1:8000/docs
echo =======================================================
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
pause

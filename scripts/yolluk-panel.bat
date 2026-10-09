@echo off
cd /d "%~dp0.."
title MYS Yolluk Otomasyon Merkezi
start "" http://127.0.0.1:8765
python scripts\yolluk-controller.py

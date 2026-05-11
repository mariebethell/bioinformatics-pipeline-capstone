@echo off

rd /s /q .\build
rd /s /q .\dist

poetry run briefcase create windows
poetry run briefcase build windows
poetry run briefcase package windows
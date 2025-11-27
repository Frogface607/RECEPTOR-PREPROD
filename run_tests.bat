@echo off
chcp 65001 >nul
echo ============================================================
echo 🚀 Запуск Backend и тестирование батчевой генерации меню
echo ============================================================
echo.

echo [1/3] Запуск Backend сервера...
start "Backend Server" cmd /k "cd backend && python -m uvicorn server:app --host 0.0.0.0 --port 8000"

echo [2/3] Ожидание запуска сервера (10 секунд)...
timeout /t 10 /nobreak >nul

echo [3/3] Запуск тестов...
python test_batch_menu_generation.py

echo.
echo ============================================================
echo ✅ Тестирование завершено!
echo ============================================================
echo.
echo Примечание: Backend сервер продолжает работать в отдельном окне.
echo Для остановки закройте окно "Backend Server" или нажмите Ctrl+C.
echo.
pause








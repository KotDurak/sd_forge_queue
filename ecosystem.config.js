module.exports = {
  apps: [
    {
      name: "sd-gateway",
      script: "uvicorn",
      args: "main:app --host 0.0.0.0 --port 8000",
      interpreter: "python", // PM2 будет использовать Python из PATH
      cwd: "D:\\sd_forge_queue", // 🔥 Замени на свой путь!
      env: {
        PYTHONPATH: "D:\\sd_forge_queue",
      },
      // Логи
      error_file: "logs/gateway-error.log",
      out_file: "logs/gateway-out.log",
      merge_logs: true,
      log_date_format: "YYYY-MM-DD HH:mm:ss",
      // Автоперезапуск
      autorestart: true,
      watch: false, // Отключаем watch, чтобы не перезапускался при каждом изменении
      max_memory_restart: "512M", // Перезапуск, если съест больше 512 МБ
      // Перезапуск при падении
      restart_delay: 4000,
    },
  ],
};
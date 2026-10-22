# Управление Cloudflare Tunnel

## Запуск/остановка туннеля (Windows)

```bash
# Через CMD (от администратора)
sc stop cloudflared      # остановить
sc start cloudflared     # запустить
sc query cloudflared     # проверить статус

# Через PowerShell (от администратора)
Stop-Service cloudflared    # остановить
Start-Service cloudflared   # запустить
Restart-Service cloudflared # перезапустить

# Через net
net stop cloudflared
net start cloudflared
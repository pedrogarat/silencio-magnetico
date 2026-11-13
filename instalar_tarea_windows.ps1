# Script para registrar la tarea en el Programador de Tareas de Windows
# Horarios diarios exactos: 08:00, 13:00, 18:00, 23:00

$TaskName = "SOMBRA_Generador_Banners_21_9"
$ScriptBat = "g:\OneDrive\ANTIGRAVITY\NOVELA_3\ejecutar_banner_cron.bat"
$WorkingDir = "g:\OneDrive\ANTIGRAVITY\NOVELA_3"

Write-Host "Configurando tarea programada de Windows con horarios exactos (08:00, 13:00, 18:00, 23:00): $TaskName"

# Acción: ejecutar el .bat minimizado/oculto
$Action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$ScriptBat`"" -WorkingDirectory $WorkingDir

# Disparadores diarios en las 4 horas deseadas
$Triggers = @(
    (New-ScheduledTaskTrigger -Daily -At "08:00"),
    (New-ScheduledTaskTrigger -Daily -At "13:00"),
    (New-ScheduledTaskTrigger -Daily -At "18:00"),
    (New-ScheduledTaskTrigger -Daily -At "23:00")
)

# Configuración: si el equipo estaba apagado a esa hora, ejecutar al encender (StartWhenAvailable)
$Settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Minutes 30)

# Registrar tarea para el usuario actual
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Triggers -Settings $Settings -Description "Genera el siguiente banner 21:9 de SOMBRA a las 08h, 13h, 18h y 23h" -Force

Write-Host "`n[OK] Tarea programada actualizada con éxito en Windows."

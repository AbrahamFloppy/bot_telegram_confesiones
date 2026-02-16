# Bot de Confesiones para Telegram

## Descripción general

Este proyecto implementa un bot de Telegram diseñado para recibir confesiones de manera anónima y enviarlas a un canal específico. El bot utiliza la API de Telegram y está desarrollado en Python. Su objetivo es permitir que los usuarios envíen mensajes sin revelar su identidad, mientras que el administrador del canal recibe las confesiones de forma organizada.

## Contenido del repositorio

| Archivo | Descripción |
|--------|-------------|
| bot.py | Script principal del bot. Contiene la lógica para recibir mensajes, reenviarlos al canal y gestionar comandos. |
| requirements.txt | Lista de dependencias necesarias para ejecutar el bot. |

## Requisitos

Para ejecutar el bot se necesita:

- Python 3.8 o superior
- Una cuenta de Telegram
- Un bot creado mediante BotFather
- Un token de acceso válido
- Un ID de canal donde se enviarán las confesiones

Instalación de dependencias:

pip install -r requirements.txt

## Configuración

1. Crear un bot en Telegram usando BotFather.
2. Obtener el token del bot.
3. Obtener el ID del canal donde se publicarán las confesiones.
4. Configurar las variables necesarias dentro del archivo bot.py.

## Uso

Ejecutar el bot con:

python bot.py

Una vez activo:

- Los usuarios pueden enviar mensajes al bot.
- El bot reenviará automáticamente cada mensaje al canal configurado.
- La identidad del usuario no se muestra en el canal.

## Funcionalidades principales

- Recepción de mensajes privados.
- Reenvío automático al canal configurado.
- Manejo de comandos básicos.
- Funcionamiento continuo mediante polling.

## Mejoras futuras

- Implementación de base de datos para estadísticas.
- Sistema de moderación previo al envío.
- Panel de administración.
- Compatibilidad con botones y menús interactivos.

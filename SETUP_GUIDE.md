
# Configuración de Credenciales de Google Cloud

Para usar la aplicación, necesitas crear tus propias credenciales de API de Google (Client ID y Client Secret). Sigue estos pasos:

## 1. Crear un Proyecto en Google Cloud
1. Ve a la [Consola de Google Cloud](https://console.cloud.google.com/).
2. Crea un **Nuevo Proyecto** (nómbralo algo como "My YTMusic CLI").

## 2. Habilitar la API de YouTube
1. En el menú lateral, ve a **APIs y servicios** > **Biblioteca**.
2. Busca "YouTube Data API v3".
3. Haz clic en **Habilitar**.

## 3. Configurar la Pantalla de Consentimiento OAuth
1. Ve a **APIs y servicios** > **Pantalla de consentimiento de OAuth**.
2. Selecciona **Externo**.
3. Rellena los campos obligatorios (nombre de la app, correo de soporte).
4. En "Scopes", puedes dejarlo por defecto o añadir `../auth/youtube`.
5. En "Usuarios de prueba", añade tu propio correo de Gmail (importante si la app no está verificada).

## 4. Crear Credenciales (Client ID y Secret)
1. Ve a **APIs y servicios** > **Credenciales**.
2. Haz clic en **Crear Credenciales** > **ID de cliente de OAuth**.
3. En "Tipo de aplicación", selecciona **TVs y dispositivos de entrada limitada**.
4. Dale un nombre y haz clic en crear.
5. Copia el **ID de cliente** y el **Secreto de cliente**.

¡Pega estos valores en la pantalla de inicio de la aplicación!

# Flutter Auth Integration

## 1. Descripcion general

Este microservicio usa dos tipos de token:

- **access token**: token de corta duracion usado para llamar APIs protegidas
- **refresh token**: token de larga duracion usado para pedir un nuevo access token sin volver a iniciar sesion

### Por que se usan ambos

El access token reduce la ventana de riesgo si un token se filtra, porque expira rapido.

El refresh token mejora la experiencia de usuario, porque permite renovar el access token sin obligar al usuario a escribir credenciales de nuevo cada poco tiempo.

---

## 2. Flujo de autenticacion

Flujo recomendado:

1. El usuario hace login
2. `ms-auth` responde con `access_token` y `refresh_token`
3. La app guarda ambos tokens de forma segura
4. La app usa el `access_token` en cada request protegido
5. Cuando el `access_token` expira, la app usa el `refresh_token`
6. `ms-auth` devuelve un nuevo `access_token`
7. La app reemplaza el token viejo y repite el request original

---

## 3. Ejemplo en Flutter

## Login

Ejemplo usando `http`:

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;

final response = await http.post(
  Uri.parse('http://127.0.0.1:8002/auth/login'),
  headers: {'Content-Type': 'application/json'},
  body: jsonEncode({
    'email': email,
    'password': password,
  }),
);
```

Si el login es correcto, la respuesta tendrá este formato:

```json
{
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

## Guardar tokens

Usa `flutter_secure_storage`:

```dart
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

final storage = FlutterSecureStorage();

await storage.write(key: 'access_token', value: accessToken);
await storage.write(key: 'refresh_token', value: refreshToken);
```

## Enviar requests protegidas

En cada request protegido agrega:

```dart
headers: {
  'Authorization': 'Bearer $accessToken'
}
```

Ejemplo:

```dart
final accessToken = await storage.read(key: 'access_token');

final response = await http.get(
  Uri.parse('http://127.0.0.1:8000/monitoring_sessions'),
  headers: {
    'Authorization': 'Bearer $accessToken',
  },
);
```

## Manejo de expiracion

Si una API responde `401`:

1. llama a `/auth/refresh`
2. actualiza el `access_token` guardado
3. repite el request original

## Refresh token

Ejemplo usando `http`:

```dart
final refreshToken = await storage.read(key: 'refresh_token');

final response = await http.post(
  Uri.parse('http://127.0.0.1:8002/auth/refresh'),
  headers: {'Content-Type': 'application/json'},
  body: jsonEncode({
    'refresh_token': refreshToken,
  }),
);
```

La respuesta esperada es:

```json
{
  "access_token": "...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

Luego debes guardar el nuevo `access_token`:

```dart
final data = jsonDecode(response.body);
await storage.write(key: 'access_token', value: data['access_token']);
```

---

## 4. Buenas practicas

- usa `flutter_secure_storage`
- no guardes tokens en texto plano
- no expongas el `refresh_token`
- renueva el `access_token` automaticamente
- elimina tokens al hacer logout
- si el refresh falla con `401`, fuerza nuevo login

---

## 5. Diagrama simple

```text
Login -> access + refresh
Access -> APIs
Expire -> Refresh -> Nuevo access
```

---

## Ejemplo de estrategia simple

Flujo recomendado en la app:

1. guardar `access_token`
2. guardar `refresh_token`
3. usar `access_token` por defecto
4. si cualquier request protegido responde `401`, intentar refresh una sola vez
5. si refresh funciona, repetir request
6. si refresh falla, cerrar sesion local y mandar al usuario a login

---

## Notas de integracion

- `/auth/me` solo acepta `access_token`
- `/auth/verify` solo acepta `access_token`
- `/auth/refresh` solo acepta `refresh_token`
- no uses el `refresh_token` para llamar MS CRUD o MS MID
- MS CRUD y MS MID deben recibir siempre el `access_token`

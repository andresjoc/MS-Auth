# Integracion de MS AUTH en Flutter

Este documento explica como integrar `ms-auth` desde una aplicacion Flutter usando `http` y `flutter_secure_storage`, con un flujo completo de autenticacion basado en `access_token` y `refresh_token`.

La idea es que un desarrollador Flutter pueda copiar este flujo casi completo, adaptando solo la URL base del backend y la navegacion de su app.

---

## 1. Que hace MS AUTH

`ms-auth` es el microservicio encargado de la autenticacion del sistema. Sus responsabilidades principales son:

- registrar usuarios
- validar credenciales
- emitir JWT
- renovar sesiones
- exponer informacion del usuario autenticado

Endpoints principales:

- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/refresh`
- `GET /auth/me`
- `GET /auth/verify`

En este proyecto, `ms-auth`:

- recibe email y password en login
- devuelve un `access_token`
- devuelve un `refresh_token`
- indica cuanto dura el `access_token` con `expires_in`

Ejemplo real de respuesta de login:

```json
{
  "access_token": "eyJhbGciOi...",
  "refresh_token": "eyJhbGciOi...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

---

## 2. Que es `access_token` y `refresh_token`

### `access_token`

Es el token que la app usa para llamar endpoints protegidos, por ejemplo:

- `GET /auth/me`
- endpoints privados de otros microservicios como `ms-crud` o `ms-mid`

Se envia normalmente en el header:

```http
Authorization: Bearer <access_token>
```

Este token debe tener una vida corta. En este backend, `expires_in` se calcula a partir de `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`.

### `refresh_token`

Es el token que la app usa para pedir un nuevo `access_token` cuando el actual expira, sin obligar al usuario a volver a escribir su email y password.

Se envia al endpoint:

- `POST /auth/refresh`

Payload real:

```json
{
  "refresh_token": "..."
}
```

Respuesta real:

```json
{
  "access_token": "nuevo_access_token",
  "token_type": "bearer",
  "expires_in": 3600
}
```

Importante: en este backend, el refresh **no devuelve un nuevo `refresh_token`**, solo un nuevo `access_token`.

### Por que se usan ambos

Se usan ambos por seguridad y experiencia de usuario.

- El `access_token` dura poco. Si se filtra, la ventana de riesgo es menor.
- El `refresh_token` permite mantener la sesion sin pedir login constantemente.

Si existiera solo un token de larga duracion para todo, el riesgo seria mayor. Si existiera solo un token de corta duracion sin refresh, el usuario tendria que iniciar sesion con demasiada frecuencia.

---

## 3. Flujo completo de autenticacion

El flujo recomendado desde Flutter es este:

1. El usuario se registra con `POST /auth/register`.
2. El usuario inicia sesion con `POST /auth/login`.
3. La app parsea `access_token`, `refresh_token` y `expires_in`.
4. La app guarda los tokens en almacenamiento seguro.
5. La app usa el `access_token` en llamadas a APIs protegidas.
6. Si el backend responde `401`, la app intenta renovar el `access_token` usando el `refresh_token`.
7. Si el refresh funciona, la app repite la llamada original.
8. Si el refresh falla, la app elimina los tokens y fuerza nuevo login.

---

## 4. Flujo de registro

Endpoint:

- `POST /auth/register`

Payload real esperado por este backend:

```json
{
  "id_city": 11001,
  "email": "ana@example.com",
  "password": "Secret123!",
  "first_name": "Ana",
  "last_name": "Lopez",
  "birth_date": "1998-04-21"
}
```

La app Flutter debe resolver la ubicacion de forma jerarquica:

- seleccionar pais
- seleccionar region
- seleccionar ciudad

Pero en el registro se envia solo `id_city`, porque el backend deduce la relacion con `region` y `country` desde esa ciudad.

Respuesta:

```json
{
  "id_user": 1,
  "id_city": 11001,
  "email": "ana@example.com",
  "first_name": "Ana",
  "last_name": "Lopez",
  "birth_date": "1998-04-21"
}
```

Ejemplo Flutter con `http`:

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;

Future<void> registerUser() async {
  final response = await http.post(
    Uri.parse('http://127.0.0.1:8002/auth/register'),
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode({
      'id_city': 11001,
      'email': 'ana@example.com',
      'password': 'Secret123!',
      'first_name': 'Ana',
      'last_name': 'Lopez',
      'birth_date': '1998-04-21',
    }),
  );

  if (response.statusCode != 201) {
    throw Exception('Error en registro: ${response.body}');
  }
}
```

---

## 5. Flujo de login

Endpoint:

- `POST /auth/login`

Payload:

```json
{
  "email": "ana@example.com",
  "password": "Secret123!"
}
```

### Ejemplo Flutter con `http.post`

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;

Future<void> loginExample(String email, String password) async {
  final response = await http.post(
    Uri.parse('http://127.0.0.1:8002/auth/login'),
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode({
      'email': email,
      'password': password,
    }),
  );

  if (response.statusCode != 200) {
    throw Exception('Login fallido: ${response.body}');
  }

  final Map<String, dynamic> data = jsonDecode(response.body);

  final String accessToken = data['access_token'];
  final String refreshToken = data['refresh_token'];
  final int expiresIn = data['expires_in'];

  print(accessToken);
  print(refreshToken);
  print(expiresIn);
}
```

### Parsear la respuesta

Los tres campos clave son:

- `access_token`: token para consumir APIs protegidas
- `refresh_token`: token para obtener un nuevo `access_token`
- `expires_in`: duracion del `access_token` en segundos

Ejemplo:

```dart
final Map<String, dynamic> json = jsonDecode(response.body);

final String accessToken = json['access_token'] as String;
final String refreshToken = json['refresh_token'] as String;
final int expiresIn = json['expires_in'] as int;
```

---

## 6. Guardar tokens con `flutter_secure_storage`

No debes guardar tokens en `SharedPreferences` si buscas un nivel de seguridad adecuado para autenticacion. Para este caso usa `flutter_secure_storage`.

Dependencia:

```yaml
dependencies:
  http: ^1.2.1
  flutter_secure_storage: ^9.2.2
```

Ejemplo de guardado:

```dart
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

const FlutterSecureStorage storage = FlutterSecureStorage();

Future<void> saveTokens({
  required String accessToken,
  required String refreshToken,
  required int expiresIn,
}) async {
  final expiresAt = DateTime.now().add(Duration(seconds: expiresIn));

  await storage.write(key: 'access_token', value: accessToken);
  await storage.write(key: 'refresh_token', value: refreshToken);
  await storage.write(
    key: 'access_token_expires_at',
    value: expiresAt.toIso8601String(),
  );
}
```

Lectura:

```dart
Future<String?> readAccessToken() {
  return storage.read(key: 'access_token');
}

Future<String?> readRefreshToken() {
  return storage.read(key: 'refresh_token');
}
```

---

## 7. Uso del token en requests protegidos

Cada vez que llames una API protegida, agrega el header `Authorization`.

```dart
final accessToken = await storage.read(key: 'access_token');

final response = await http.get(
  Uri.parse('http://127.0.0.1:8002/auth/me'),
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer $accessToken',
  },
);
```

Si consumes otros microservicios del ecosistema, el patron es el mismo:

```http
Authorization: Bearer <access_token>
```

---

## 8. Expiracion del token

El backend devuelve `expires_in`, por ejemplo `3600`. Eso significa que el `access_token` dura 3600 segundos desde el momento en que fue emitido.

En la app conviene guardar una fecha calculada de expiracion:

```dart
final expiresAt = DateTime.now().add(Duration(seconds: expiresIn));
await storage.write(
  key: 'access_token_expires_at',
  value: expiresAt.toIso8601String(),
);
```

Con eso puedes:

- intentar refresh antes de que expire
- o reaccionar cuando un request falle con `401`

Ambos enfoques son validos. En mobile, lo mas simple y robusto suele ser:

- verificar si el token ya expiro antes del request
- si aun no sabes, intentar el request
- si responde `401`, hacer refresh

---

## 9. Refresh token

Endpoint:

- `POST /auth/refresh`

Payload:

```json
{
  "refresh_token": "..."
}
```

Ejemplo Flutter:

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

const FlutterSecureStorage storage = FlutterSecureStorage();

Future<String> refreshAccessToken() async {
  final refreshToken = await storage.read(key: 'refresh_token');

  if (refreshToken == null || refreshToken.isEmpty) {
    throw Exception('No hay refresh token disponible');
  }

  final response = await http.post(
    Uri.parse('http://127.0.0.1:8002/auth/refresh'),
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode({
      'refresh_token': refreshToken,
    }),
  );

  if (response.statusCode != 200) {
    throw Exception('No se pudo renovar el token: ${response.body}');
  }

  final Map<String, dynamic> data = jsonDecode(response.body);
  final newAccessToken = data['access_token'] as String;
  final expiresIn = data['expires_in'] as int;

  final expiresAt = DateTime.now().add(Duration(seconds: expiresIn));

  await storage.write(key: 'access_token', value: newAccessToken);
  await storage.write(
    key: 'access_token_expires_at',
    value: expiresAt.toIso8601String(),
  );

  return newAccessToken;
}
```

---

## 10. Manejo de errores

### Error `401 Unauthorized`

Un `401` normalmente significa una de estas cosas:

- el `access_token` expiro
- el token es invalido
- el token no fue enviado
- el usuario fue desactivado

Accion recomendada:

1. intentar refresh una sola vez
2. si refresh funciona, repetir el request
3. si refresh falla con `401`, cerrar sesion local y mandar al login

### Token expirado

En este backend, cuando un token es invalido o expiro, la respuesta puede incluir mensajes como:

- `Invalid or expired token`
- `Invalid credentials`
- `Inactive user`

No dependas del texto exacto para la logica de la app. La decision principal debe basarse en el `statusCode`.

Ejemplo de criterio:

```dart
if (response.statusCode == 401) {
  // intentar refresh o cerrar sesion
}
```

---

## 11. Buenas practicas

- No guardes tokens en texto plano.
- Usa `flutter_secure_storage`.
- No imprimas tokens en logs de produccion.
- No expongas el `refresh_token` en UI, analytics o errores.
- No uses el `refresh_token` para llamar APIs de negocio.
- Usa siempre el `access_token` para endpoints protegidos.
- Elimina ambos tokens al hacer logout.
- Si el refresh falla, obliga al usuario a autenticarse de nuevo.
- Si tienes varias llamadas concurrentes, evita disparar multiples refresh al mismo tiempo.

---

## 12. Codigo completo listo para copiar

### Modelo de respuesta de login

```dart
class LoginResponse {
  final String accessToken;
  final String refreshToken;
  final String tokenType;
  final int expiresIn;

  LoginResponse({
    required this.accessToken,
    required this.refreshToken,
    required this.tokenType,
    required this.expiresIn,
  });

  factory LoginResponse.fromJson(Map<String, dynamic> json) {
    return LoginResponse(
      accessToken: json['access_token'] as String,
      refreshToken: json['refresh_token'] as String,
      tokenType: json['token_type'] as String,
      expiresIn: json['expires_in'] as int,
    );
  }
}
```

### Modelo de respuesta de refresh

```dart
class RefreshResponse {
  final String accessToken;
  final String tokenType;
  final int expiresIn;

  RefreshResponse({
    required this.accessToken,
    required this.tokenType,
    required this.expiresIn,
  });

  factory RefreshResponse.fromJson(Map<String, dynamic> json) {
    return RefreshResponse(
      accessToken: json['access_token'] as String,
      tokenType: json['token_type'] as String,
      expiresIn: json['expires_in'] as int,
    );
  }
}
```

### Clase `AuthService`

```dart
import 'dart:convert';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;

class AuthService {
  AuthService({
    required this.baseUrl,
    http.Client? client,
    FlutterSecureStorage? storage,
  })  : _client = client ?? http.Client(),
        _storage = storage ?? const FlutterSecureStorage();

  final String baseUrl;
  final http.Client _client;
  final FlutterSecureStorage _storage;

  static const String _accessTokenKey = 'access_token';
  static const String _refreshTokenKey = 'refresh_token';
  static const String _accessTokenExpiresAtKey = 'access_token_expires_at';

  Future<void> login({
    required String email,
    required String password,
  }) async {
    final response = await _client.post(
      Uri.parse('$baseUrl/auth/login'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'email': email,
        'password': password,
      }),
    );

    if (response.statusCode != 200) {
      throw Exception('Login fallido: ${response.body}');
    }

    final Map<String, dynamic> data = jsonDecode(response.body);
    final accessToken = data['access_token'] as String;
    final refreshToken = data['refresh_token'] as String;
    final expiresIn = data['expires_in'] as int;

    await _saveTokens(
      accessToken: accessToken,
      refreshToken: refreshToken,
      expiresIn: expiresIn,
    );
  }

  Future<String> refreshToken() async {
    final storedRefreshToken = await _storage.read(key: _refreshTokenKey);

    if (storedRefreshToken == null || storedRefreshToken.isEmpty) {
      throw Exception('No hay refresh token disponible');
    }

    final response = await _client.post(
      Uri.parse('$baseUrl/auth/refresh'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'refresh_token': storedRefreshToken,
      }),
    );

    if (response.statusCode == 401) {
      await logout();
      throw Exception('Refresh token invalido o expirado');
    }

    if (response.statusCode != 200) {
      throw Exception('Error al refrescar token: ${response.body}');
    }

    final Map<String, dynamic> data = jsonDecode(response.body);
    final accessToken = data['access_token'] as String;
    final expiresIn = data['expires_in'] as int;

    final expiresAt = DateTime.now().add(Duration(seconds: expiresIn));

    await _storage.write(key: _accessTokenKey, value: accessToken);
    await _storage.write(
      key: _accessTokenExpiresAtKey,
      value: expiresAt.toIso8601String(),
    );

    return accessToken;
  }

  Future<String?> getAccessToken() async {
    final accessToken = await _storage.read(key: _accessTokenKey);
    final expiresAtString =
        await _storage.read(key: _accessTokenExpiresAtKey);

    if (accessToken == null || expiresAtString == null) {
      return null;
    }

    final expiresAt = DateTime.tryParse(expiresAtString);
    if (expiresAt == null) {
      return accessToken;
    }

    final isExpired = DateTime.now().isAfter(expiresAt);
    if (!isExpired) {
      return accessToken;
    }

    return refreshToken();
  }

  Future<void> logout() async {
    await _storage.delete(key: _accessTokenKey);
    await _storage.delete(key: _refreshTokenKey);
    await _storage.delete(key: _accessTokenExpiresAtKey);
  }

  Future<http.Response> authenticatedGet(String endpoint) async {
    String? accessToken = await getAccessToken();

    if (accessToken == null) {
      throw Exception('El usuario no esta autenticado');
    }

    http.Response response = await _client.get(
      Uri.parse('$baseUrl$endpoint'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $accessToken',
      },
    );

    if (response.statusCode == 401) {
      accessToken = await refreshToken();

      response = await _client.get(
        Uri.parse('$baseUrl$endpoint'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $accessToken',
        },
      );
    }

    return response;
  }

  Future<void> _saveTokens({
    required String accessToken,
    required String refreshToken,
    required int expiresIn,
  }) async {
    final expiresAt = DateTime.now().add(Duration(seconds: expiresIn));

    await _storage.write(key: _accessTokenKey, value: accessToken);
    await _storage.write(key: _refreshTokenKey, value: refreshToken);
    await _storage.write(
      key: _accessTokenExpiresAtKey,
      value: expiresAt.toIso8601String(),
    );
  }
}
```

---

## 13. Ejemplo de uso de `AuthService`

```dart
final authService = AuthService(
  baseUrl: 'http://127.0.0.1:8002',
);
```

### Login

```dart
await authService.login(
  email: 'ana@example.com',
  password: 'Secret123!',
);
```

### Obtener token valido

```dart
final token = await authService.getAccessToken();
print(token);
```

### Consumir endpoint protegido

```dart
final response = await authService.authenticatedGet('/auth/me');

if (response.statusCode == 200) {
  print(response.body);
} else {
  print('Error: ${response.statusCode}');
}
```

### Logout

```dart
await authService.logout();
```

---

## 14. Ejemplo de flujo real

Flujo completo esperado:

1. El usuario hace login.
2. Flutter recibe `access_token`, `refresh_token` y `expires_in`.
3. Flutter guarda los tokens con `flutter_secure_storage`.
4. La app llama APIs protegidas usando `Authorization: Bearer <access_token>`.
5. Si el token aun es valido, la API responde normalmente.
6. Si el token expiro, la API puede responder `401`.
7. La app usa el `refresh_token` en `POST /auth/refresh`.
8. `ms-auth` devuelve un nuevo `access_token`.
9. La app guarda el nuevo `access_token`.
10. La app repite automaticamente la llamada original.
11. Si el refresh falla, la app borra sesion y redirige al login.

Representacion simple:

```text
Login
  -> guardar access_token
  -> guardar refresh_token
  -> guardar expires_at
  -> usar API protegida
  -> si 401, refresh
  -> guardar nuevo access_token
  -> reintentar request
  -> si refresh falla, logout
```

---

## 15. Recomendaciones finales de implementacion

- Centraliza toda la autenticacion en una sola clase como `AuthService`.
- No dupliques logica de refresh en cada pantalla.
- Mantene una sola fuente de verdad para los tokens.
- Usa `getAccessToken()` antes de requests protegidos.
- Reintenta solo una vez despues de refresh para evitar loops infinitos.
- Si vas a consumir varios microservicios, reutiliza el mismo `access_token`.
- Si tu app tiene estado global, sincroniza el logout con la navegacion al login.

---

## 16. Resumen practico

En Flutter, la integracion correcta con `ms-auth` consiste en:

- hacer login con `http.post`
- parsear `access_token`, `refresh_token` y `expires_in`
- guardar tokens en `flutter_secure_storage`
- usar `access_token` para endpoints protegidos
- renovar automaticamente con `refresh_token` cuando haya expiracion o `401`
- cerrar sesion si el refresh ya no funciona

Con este flujo tienes una autenticacion mobile completa, segura y alineada con el comportamiento real de este backend.

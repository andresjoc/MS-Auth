# ms-auth

Microservicio independiente de autenticación para el ecosistema PPG.

Responsabilidades:

- registrar usuarios,
- almacenar credenciales autenticables,
- validar contraseña,
- emitir JWT,
- validar JWT localmente,
- exponer el usuario autenticado.

No procesa señales PPG, no maneja métricas clínicas y no debe recibir contraseñas desde otros microservicios.

---

## Cambio de modelo de datos

Este servicio ya no usa una tabla propia `auth_user`.

Ahora trabaja con el esquema compartido del sistema:

- `app_user`: identidad principal del usuario
- `auth_credential`: credenciales de autenticación

### Fuente de identidad

La tabla `app_user` es la única fuente de identidad. Desde allí se usan:

- `id_user`
- `email`
- `first_name`
- `last_name`
- `birth_date`
- `created_at`
- `updated_at`

### Tabla de credenciales

`auth_credential` contiene:

- `id_credential`
- `id_user`
- `password_hash`
- `is_active`
- `created_at`
- `updated_at`

### Relación

- un `app_user` tiene una `auth_credential`
- `auth_credential.id_user` referencia `app_user.id_user`

### Implicación importante

`ms-auth` y `ms-crud` deben apuntar a la misma base de datos o al mismo esquema donde exista `app_user`.

`ms-auth` es el único servicio que accede a `auth_credential`.

---

## Variables de entorno

```env
AUTH_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/PPG_DB
JWT_SECRET_KEY=replace-with-a-long-random-secret
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30
AUTH_SERVICE_PORT=8002
FRONTEND_URL=http://localhost:3000
```

### Descripción

- `AUTH_DATABASE_URL`: conexión a la base donde viven `app_user` y `auth_credential`
- `JWT_SECRET_KEY`: secreto compartido con los otros microservicios
- `JWT_ALGORITHM`: algoritmo de firma; el valor esperado es `HS256`
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`: tiempo de vida del access token
- `AUTH_SERVICE_PORT`: puerto del servicio
- `FRONTEND_URL`: origen permitido para CORS

---

## Instalación

```bash
pip install -r requirements.txt
```

---

## Ejecución

```bash
uvicorn main:app --reload --port 8002
```

El servicio quedará disponible en:

- [http://127.0.0.1:8002](http://127.0.0.1:8002)

Documentación automática:

- [http://127.0.0.1:8002/docs](http://127.0.0.1:8002/docs)
- [http://127.0.0.1:8002/redoc](http://127.0.0.1:8002/redoc)

---

## Endpoints

- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/refresh`
- `GET /auth/me`
- `GET /auth/verify`
- `GET /`

---

## Comportamiento de registro

`POST /auth/register` ahora hace esto:

1. busca si el email ya existe en `app_user`
2. crea primero el registro en `app_user`
3. crea después el registro en `auth_credential`
4. guarda la contraseña solo como `password_hash`

### Payload esperado

Ahora `birth_date` es obligatorio porque forma parte del modelo compartido `app_user`.
Tambien `id_city` es obligatorio porque `MS AUTH` crea el registro completo en `app_user`.
La ubicacion se resuelve por jerarquia `city -> region -> country`, pero el registro persiste solo `id_city`.

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

### Respuesta

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

---

## Comportamiento de login

`POST /auth/login` ahora:

1. busca el usuario por email en `app_user`
2. obtiene el `password_hash` desde `auth_credential`
3. valida la contraseña
4. verifica que `auth_credential.is_active` sea `true`
5. emite un `access_token`
6. emite un `refresh_token`

El JWT incluye:

- `sub`: `id_user` como string
- `email`
- `exp`
- `type`: `access`

El refresh token incluye:

- `sub`: `id_user` como string
- `email`
- `exp`
- `type`: `refresh`

### Respuesta de login

```json
{
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

---

## Endpoint de refresh

`POST /auth/refresh` recibe:

```json
{
  "refresh_token": "..."
}
```

Comportamiento:

1. valida firma y expiracion
2. verifica que `type == "refresh"`
3. valida que el usuario siga activo
4. genera un nuevo `access_token`

Respuesta:

```json
{
  "access_token": "...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

---

## Ejemplos de curl

### Register

```bash
curl -X POST http://127.0.0.1:8002/auth/register \
  -H "Content-Type: application/json" \
  -d "{\"id_city\":11001,\"email\":\"ana@example.com\",\"password\":\"Secret123!\",\"first_name\":\"Ana\",\"last_name\":\"Lopez\",\"birth_date\":\"1998-04-21\"}"
```

### Login

```bash
curl -X POST http://127.0.0.1:8002/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"ana@example.com\",\"password\":\"Secret123!\"}"
```

### Refresh

```bash
curl -X POST http://127.0.0.1:8002/auth/refresh \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\":\"YOUR_REFRESH_TOKEN\"}"
```

### Me

```bash
curl http://127.0.0.1:8002/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Verify

```bash
curl http://127.0.0.1:8002/auth/verify \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## Seguridad

- nunca se guarda contraseña en texto plano
- nunca se devuelve `password_hash`
- el hash se guarda solo en `auth_credential`
- `app_user` queda como fuente de identidad
- `ms-auth` sigue siendo el único emisor de JWT
- `/auth/me` y `/auth/verify` aceptan solo access token
- `/auth/refresh` acepta solo refresh token
- `ms-mid` y `ms-crud` deben validar el token localmente con el mismo secreto

---

## Integración con MS MID y MS CRUD

El frontend se autentica contra `ms-auth` y luego reenvía el JWT a los otros servicios:

```http
Authorization: Bearer <token>
```

MS MID y MS CRUD:

- no deben conocer contraseñas,
- no deben llamar a `ms-auth` por request,
- deben validar firma y expiración localmente,
- deben usar el mismo `JWT_SECRET_KEY` y `JWT_ALGORITHM`.

Para eso se incluye `dependencies/auth_guard.py`, pensado para copiarse en otros servicios.

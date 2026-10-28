# 💈BarberFlow - Sistema de Gestión de Citas y Barbería

BarberFlow es una aplicación web desarrollada para la gestión eficiente de citas, servicios, barberos y control de ingresos en una barbería. Permite a los clientes agendar citas en línea con validaciones de horario y disponibilidad, y ofrece un panel de administración protegido para el control del negocio.

##Características Principales

- **Vista del Cliente (`index.html`):** 
  - Selección de servicios y barberos en tiempo real.
  - Validación automática de horario de atención (9:00 AM - 7:00 PM).
  - Control de redundancia: El sistema impide empalmes de horarios para un mismo barbero.
- **Panel de Administración (`admin.html`):**
  - Autenticación segura basada en tokens.
  - Registro, edición y eliminación de servicios y barberos.
  - Agenda general de citas con opciones para marcar como atendidas, cancelar o eliminar.
  - Control de caja / ingresos totales generados por citas completadas.
  - Modificación de credenciales de acceso (usuario y contraseña).
- **Diseño Responsivo y Consistente:** Interfaz moderna desarrollada con un tema oscuro uniforme mediante variables CSS.

## Tecnologías Utilizadas

- **Backend:** Python con **FastAPI** y **Uvicorn**.
- **Base de Datos:** **SQLite** (`barberflow.db`) con soporte para llaves foráneas.
- **Frontend:** HTML5, CSS3 y JavaScript moderno con peticiones `fetch`.
- **Despliegue en la Nube:** **Render**.

## 🌐 Enlace a la Aplicación en Producción
- [Visitar BarberFlow en la Nube](https://barberflow-miox.onrender.com)
- [Acceso al Panel de Administración](https://barberflow-miox.onrender.com/login.html) *(Usuario por defecto: admin / admin123)*

# Conflict Zero - Integración Zapier

Conecta Conflict Zero con más de 5,000 aplicaciones a través de Zapier.

## Acciones Disponibles

### Verificar RUC
Verifica un RUC peruano y obtén datos completos de la empresa.

**Entradas:**
- RUC (string, requerido)

**Salidas:**
- RUC, nombre, estado, risk_score, compliance_score, sello_status

### Comparar Empresas
Compara hasta 10 empresas por RUC.

**Entradas:**
- Lista de RUCs (array, requerido)

**Salidas:**
- comparison_id, best_option, ranking

### Agregar a Red
Agrega un proveedor a tu red de monitoreo.

**Entradas:**
- RUC (string, requerido)
- Nombre (string, requerido)
- Etiquetas (array, opcional)

## Triggers Disponibles

### Nueva Alerta
Se dispara cuando hay una nueva alerta de monitoreo.

**Filtros:**
- Severidad mínima (low, medium, high, critical)

### Cambio en Proveedor
Se dispara cuando se detecta un cambio en un proveedor.

**Filtros:**
- Tipos de cambio específicos

## Búsquedas Disponibles

### Buscar Empresa
Busca una empresa por RUC o nombre.

## Configuración

1. Obtén tu API key desde [Conflict Zero Dashboard](https://app.conflictzero.com/settings/api)
2. En Zapier, busca "Conflict Zero"
3. Conecta tu cuenta ingresando la API key
4. Crea Zaps con las acciones/triggers disponibles

## Ejemplos de Uso

### Slack + Conflict Zero
1. **Trigger**: Nueva Alerta (severity: high)
2. **Action**: Enviar mensaje a Slack #compliance

### Google Sheets + Conflict Zero
1. **Trigger**: Nueva fila en Sheets (RUCs)
2. **Action**: Verificar RUC
3. **Action**: Guardar resultados en Sheets

### Email + Conflict Zero
1. **Trigger**: Nueva Alerta
2. **Action**: Enviar email vía Gmail

## Soporte

- Email: integrations@conflictzero.com
- Documentación: https://conflictzero.com/docs/zapier

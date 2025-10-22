# Plantillas JSON para Proveedores

## Estructura de una Plantilla

Cada plantilla JSON debe contener la siguiente estructura:

```json
{
    "proveedor_id": "PROV_001",
    "nombre_proveedor": "Nombre del Proveedor",
    "imagen_referencia": "ruta/a/imagen/referencia.png",
    "dpi_imagen": 300,
    "campos": [
        {
            "nombre": "nombre_del_campo",
            "coordenadas": [x1, y1, x2, y2],
            "tipo": "texto|fecha|numerico",
            "coordenadas_pixeles": [x_min, y_min, x_max, y_max]
        }
    ]
}
```

## Campos Disponibles

### Campos Comunes en Facturas

- **NIF_Proveedor**: Identificación fiscal del proveedor
- **Fecha_Factura**: Fecha de emisión de la factura
- **Numero_Factura**: Número único de la factura
- **Total_Factura**: Importe total a pagar
- **Base_Imponible**: Base imponible antes de impuestos
- **IVA**: Importe del IVA
- **Nombre_Cliente**: Nombre del cliente facturado
- **Direccion_Cliente**: Dirección del cliente
- **Concepto**: Descripción de productos/servicios
- **Forma_Pago**: Método de pago

### Tipos de Campo

- **texto**: Cadenas de texto (nombres, direcciones, conceptos)
- **fecha**: Fechas (se intentará parsear automáticamente)
- **numerico**: Números (importes, cantidades)

## Coordenadas

- **coordenadas**: Array [x1, y1, x2, y2] en puntos PDF (72 puntos = 1 pulgada)
- **coordenadas_pixeles**: Array [x_min, y_min, x_max, y_max] en píxeles de la imagen de referencia

## Convenciones de Nomenclatura

- Usar snake_case para nombres de campos
- Prefijo del proveedor en el ID: PROV_001, PROV_002, etc.
- Nombres descriptivos y únicos para cada campo
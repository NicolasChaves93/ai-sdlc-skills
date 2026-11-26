# Simulador de procesos — guía de uso

Sirve para **probar cómo funcionaría un proceso antes de construirlo**. Tomas el dibujo del proceso (los pasos y quién hace cada uno), le dices cuánto tarda cada cosa, y el simulador te muestra:

- cuánto dura todo,
- dónde se va el tiempo,
- si alguien se vuelve un cuello de botella,
- qué situaciones raras hay que tener previstas.

**Importante:** el simulador no adivina. Sus resultados valen lo que valgan los tiempos y probabilidades que le pongas.

Para detalles de programación, mira [TECNICO.md](TECNICO.md).

## 1. Abrirlo

En una terminal:

```bash
~/proyectos/ai-sdlc-skills/sim-template/run.sh <carpeta-de-tu-simulación> 8101
```
Después abre **http://127.0.0.1:8101** en el navegador. Para cerrarlo, `Ctrl+C` en la terminal. La primera vez tarda más porque instala lo necesario.

Ejemplo del sorteo: `~/proyectos/sim-juegos/v4/ver.sh`

## 2. Cinco palabras que vas a ver

| Palabra | Qué quiere decir |
|---|---|
| **Caso** | Una vez completa del proceso (por ejemplo, un evento). **No es una persona.** Una base de 500 nombres sigue siendo un solo caso. |
| **Recurso** | Quien hace los pasos: una persona, un equipo o el sistema. |
| **Cola** | Cosas esperando porque quien las atiende está ocupado. |
| **Escenario** | Todos los números de una prueba. |
| **Semilla** | El "número del azar". Con la misma semilla sale lo mismo. |

## 3. La pantalla

**Arriba**
- **Subprocesos** muestra el proceso por partes. Haz clic en la **flecha azul** para entrar a una caja y usa la ruta de arriba para volver.
- **▶** reproduce lo que pasó. **10× … 1000×** es la velocidad.
- **⟲** vuelve a los valores originales de la parte que estás viendo.

**Sobre el dibujo**
- **Simular:** elige todo el proceso o solo una parte.
- **Mapa de calor:** pinta los pasos que más pesan.

**Izquierda: tus controles**
- **Flujo:** al azar, mejor caso o peor caso.
- **🎲 Otra:** muestra otra forma en que podría salir.
- **Resultado:** duración y datos principales.
- **Escenario:** los valores que puedes mover, agrupados por tema.

**Derecha: cuatro pestañas**

| Pestaña | Para qué |
|---|---|
| **Puntos críticos** | Alertas, dónde se va el tiempo, casos raros y sugerencias para probar. |
| **Paso** | Haz clic en una caja o un rombo y cambia cómo funciona. |
| **Pruebas** | Comparar, subir la carga, escenarios aleatorios y revisión del recorrido. |
| **Guardados** | Guardar lo que pasó, volver a cargarlo y comparar. |

### Las etiquetas de cada valor
- **negocio:** es una regla de tu producto.
- **real:** lo mediste o lo confirmaste.
- **supuesto:** todavía no lo sabes; es un estimado.

El valor con el que arranca debe ser **tu situación real**. Lo que quieras probar, muévelo en pantalla y vuelve con **⟲**.

### Cómo sacar una probabilidad
**Veces que pasó ÷ veces que podía pasar.** Si de 20 sorteados ganaron 5: 5 ÷ 20 = **0,25** (2,5 de cada 10).

0 es nunca y 1 es siempre. Con menos de unas 20 observaciones es apenas una idea: prueba también un valor más bajo y otro más alto.

## 4. Quiero saber…

| Pregunta | Qué hago |
|---|---|
| **¿Cuánto tarda normalmente?** | Pruebas → *Comparar mejor / azar / peor*. Mira la mediana, no una sola corrida. |
| **¿Dónde se va el tiempo?** | Puntos críticos → *Dónde se va el tiempo*. |
| **¿Necesito otra persona?** | Sube los casos al mismo tiempo y mira *Alertas* y *Sugerencia*. Con un solo caso nadie hace fila. |
| **¿Y si la base fuera de 5 000?** | Cambia el valor, o usa Puntos críticos → *Sugerencias para probar datos reales* (al final) → **Probar**. |
| **¿Y si algo falla?** | Clic en el rombo → **Forzar camino**. |
| **¿Qué debo probar sí o sí?** | Puntos críticos → *Casos borde a probar*. |

### Cambiar cómo funciona un paso
Clic en la caja, pestaña **Paso**:
- **Cuánto tarda:** fijo, entre dos valores, o "humano" (casi siempre cerca de la media y a veces mucho más).
- **Quién lo hace.**
- **Restablecer este paso** lo deja como estaba.

Los tiempos van en **segundos**. Para cambiar los pasos o las flechas hay que modificar el dibujo, no el simulador.

## 5. Guardar lo que pasó y ver si se soluciona

1. En **Simular:** elige la parte.
2. Pon en pantalla lo que ocurrió.
3. **Guardados** → nombre ("Evento 28/10, se alargó") y una nota → **Guardar**.
4. Cuando quieras, **Cargar**.
5. Cambia lo que propones mejorar.
6. **Comparar con lo de ahora:** ves antes, después y qué cambiaste.

Que mejore en el simulador **no garantiza** que mejore en la vida real. Confírmalo en el siguiente evento y guarda lo que pase.

## 6. Escenarios aleatorios

Pruebas → **Escenarios aleatorios**. Cambia al azar solo los **supuestos** (también los tiempos de cada paso). Lo real y las reglas no se tocan.

1. Elige cuántos escenarios y cuánto pueden variar.
2. Si quieres, pon una **meta** ("que dure máximo 45 minutos").
3. Verás el rango de resultados, en cuántos se cumple la meta, **qué pesa más** y los mejores y peores casos. *Aplicar en pantalla* carga uno.

Los porcentajes **no son probabilidades reales**: dependen de cuánto dejes variar los supuestos.

### Ver qué cambió y moverlo a mano
Al aplicar un escenario (o cargar uno guardado) se abre la ventana **Cambios**: por cada valor muestra la **base**, lo de **ahora** (puedes escribir otro) y **↺** para devolver solo ese. La cierras con **✕** y la vuelves a abrir con el botón **Cambios (n)**, sobre el dibujo.

## 7. Pedirle ideas a una IA

El simulador deja los resultados dentro de la carpeta de la simulación. Los dos primeros **se reemplazan**, así que no se acumulan:

| Archivo | Qué trae |
|---|---|
| `reports/ultimo_resultado.json` | La última prueba que viste y, segundos después, el rango de 30 repeticiones. |
| `reports/exploracion.json` | Los últimos escenarios aleatorios. |
| `escenarios_guardados/` | Los que guardaste tú, uno por archivo. Para borrar uno, borra su archivo. |

Pide, por ejemplo:
> Lee el último resultado y propón mejoras. Separa lo que depende de supuestos y no cambies diagramas sin mi aprobación.

## 8. Cosas que confunden

| Lo que ves | Por qué |
|---|---|
| **Ráfaga +10** crea colas enormes | Son 10 procesos más compitiendo por las mismas personas. Úsalo solo si de verdad llegan muchos a la vez. |
| No aparece la sugerencia de capacidad | No hay fila, y entonces sumar gente no ayuda. |
| Un camino sale en **0 %** | En esa corrida no ocurrió. Prueba **🎲 Otra** o fórzalo. |
| «El registro cumple el BPMN» | El recorrido simulado sigue las flechas. No significa que el proceso sea correcto. |
| No veo un cambio | Recarga la página (F5). |
| «No hay conexión con el motor» | El simulador está apagado: vuelve a abrirlo (punto 1). |
| La página dice que el escenario cambió | Cambiaron los valores originales y se restauraron. |

## 9. Hacer la simulación de otro proceso

No hace falta programar. Lo más fácil es pedírselo al asistente:

> Crea la simulación de este proceso con el estándar de `sim-template`: diagramas con carriles, numerados y sin errores, y un escenario con etiquetas real, negocio y supuesto.

Ten a mano:
1. **Los pasos** y **quién** hace cada uno.
2. **Cuándo** ocurre cada tramo (por ejemplo, preparar el día antes y ejecutar el día del evento).
3. **Cuánto tarda** cada paso, aunque sea aproximado.
4. **Cada cuánto** pasa cada alternativa.
5. Qué datos son **reales** y cuáles supones.

Cómo debe quedar cada diagrama está en [TECNICO.md](TECNICO.md#estándar-de-diagramas).

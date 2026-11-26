// Detiene la preparación si el BPMN usa algo que el simulador no respeta: sin esto se descartaría o se simularía
// como instantáneo sin avisar, y se probaría un flujo distinto del dibujado.
// Uso (desde la carpeta del espacio de trabajo): node check-supported.mjs <modelo>
import fs from 'node:fs';
import { DOMParser } from '@xmldom/xmldom';
import { BPMN, local } from './layout.mjs';

const model = process.argv[2];
const doc = new DOMParser().parseFromString(fs.readFileSync(`models/${model}.bpmn`, 'utf8'), 'text/xml');
const MOTIVOS = [
  [/EventDefinition$/, 'eventos con temporizador, mensaje, señal, error o terminación'],
  [/^boundaryEvent$/, 'eventos de borde'],
  [/LoopCharacteristics$/, 'repeticiones y multi-instancia'],
  [/^(sendTask|receiveTask|scriptTask|businessRuleTask|callActivity)$/, 'este tipo de tarea (usa tarea, de usuario, manual o de servicio)'],
  [/^conditionExpression$/, 'condiciones en las flechas (las rutas salen de las probabilidades del escenario)'],
];
const errores = [];
for (const e of [...doc.getElementsByTagNameNS(BPMN, '*')]) {
  const motivo = MOTIVOS.find(([re]) => re.test(local(e)));
  if (!motivo) continue;
  const dueño = e.getAttribute('id') && !/EventDefinition|LoopCharacteristics/.test(local(e)) ? e : e.parentNode;
  errores.push(`  - ${dueño.getAttribute('name') || '(sin nombre)'} [${dueño.getAttribute('id')}]: ${motivo[1]}`);
}
if (errores.length) {
  console.error(`El simulador todavía no admite esto de models/${model}.bpmn:\n${errores.join('\n')}\nNo se generó ningún modelo.`);
  process.exit(1);
}

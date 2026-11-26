import Viewer from 'bpmn-js/lib/Viewer';
const v = new Viewer({ container: '#c' });
v.importXML(document.getElementById('xml').textContent).then(() => { v.get('canvas').zoom('fit-viewport', 'center'); document.title = 'LISTO'; });
